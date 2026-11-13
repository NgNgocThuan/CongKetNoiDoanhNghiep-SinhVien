"""Offline PDF signatures. Missing trust/signing material always fails closed."""
from io import BytesIO

from app.core.config import settings
from app.core.exceptions import AppException, BadRequestError


def ready():
    return bool(settings.MOU_SCHOOL_PFX_PATH and settings.MOU_TRUST_ROOT_PATH)


def signing_material():
    if not ready():
        raise AppException("Nhà trường chưa cấu hình chứng thư ký số MOU. Bạn có thể sử dụng phương án ký giấy.", code="MOU_SIGNING_NOT_READY", status_code=503)
    try:
        from pyhanko.sign import signers
        signer = signers.SimpleSigner.load_pkcs12(
            settings.MOU_SCHOOL_PFX_PATH,
            passphrase=settings.MOU_SCHOOL_PFX_PASSWORD.encode() or None,
        )
        if signer is None:
            raise ValueError("Missing signer")
        return signer
    except Exception:
        raise AppException("Không thể tải chứng thư ký số của Nhà trường.", code="MOU_SIGNING_NOT_READY", status_code=503) from None


def sign_template(pdf_bytes, company):
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign import signers
    from pyhanko.sign.fields import MDPPerm
    signer = signing_material()
    writer = IncrementalPdfFileWriter(BytesIO(pdf_bytes))
    from pyhanko.pdf_utils import generic
    writer.set_info(generic.DictionaryObject({
        generic.pdf_name("/Subject"): generic.pdf_string(f"StudentConnect:MOU:{company.id}:{company.tax_code}"),
    }))
    return signers.sign_pdf(
        writer,
        signers.PdfSignatureMetadata(field_name="SchoolSignature", certify=True, docmdp_permissions=MDPPerm.FILL_FORMS),
        signer=signer,
    ).getvalue()


def validate_company_pdf(pdf_bytes, company):
    signer = signing_material()
    try:
        from pyhanko.keys import load_cert_from_pemder
        from pyhanko.pdf_utils.reader import PdfFileReader
        from pyhanko.sign.validation import validate_pdf_signature
        from pyhanko_certvalidator import ValidationContext
        reader = PdfFileReader(BytesIO(pdf_bytes))
        signatures = reader.embedded_signatures
        if len(signatures) != 2:
            raise ValueError("Two signatures required")
        school, business = signatures
        if school.signer_cert.dump() != signer.signing_cert.dump():
            raise ValueError("Unknown school")
        if school.signer_cert.dump() == business.signer_cert.dump():
            raise ValueError("Distinct signers required")
        context_options = dict(
            trust_roots=[load_cert_from_pemder(settings.MOU_TRUST_ROOT_PATH), signer.signing_cert],
            allow_fetching=False, revocation_mode="require", crls=[], ocsps=[],
        )
        if "/DSS" in reader.root:
            from pyhanko.sign.validation.dss import DocumentSecurityStore
            context = DocumentSecurityStore.read_dss(reader).as_validation_context(context_options)
        else:
            context = ValidationContext(**context_options)
        for signature in signatures:
            status = validate_pdf_signature(signature, signer_validation_context=context)
            if not (status.bottom_line and status.intact and status.valid and status.trusted and status.docmdp_ok):
                raise ValueError("Invalid or untrusted signature")
        if reader.trailer["/Info"]["/Subject"] != f"StudentConnect:MOU:{company.id}:{company.tax_code}":
            raise ValueError("Wrong agreement")
        subject = business.signer_cert.subject.native
        identifiers = [str(subject.get(key, "")) for key in ("serial_number", "user_id", "organization_identifier")]
        expected = company.tax_code
        if not expected or not any(value in (expected, f"MST:{expected}", f"MST: {expected}", f"TIN:{expected}") for value in identifiers):
            raise ValueError("Tax code mismatch")
        return str(subject.get("common_name", "")), expected, business.signer_cert.issuer.human_friendly
    except Exception as exc:
        raise BadRequestError("MOU cần đủ hai chữ ký tin cậy, bằng chứng hiệu lực chứng thư và đúng mã số thuế; nội dung không được thay đổi.", code="MOU_SIGNATURE_INVALID") from exc
