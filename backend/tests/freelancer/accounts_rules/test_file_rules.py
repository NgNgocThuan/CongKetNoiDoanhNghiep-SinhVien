import unittest

from app.services.freelancer_accounts import file_rules as f

POLICY = f.DOCUMENT_POLICY
PDF_HEAD = b"%PDF-1.7\n" + b"x" * 8
PNG_HEAD = b"\x89PNG\r\n\x1a\n" + b"x" * 8
JPG_HEAD = b"\xff\xd8\xff\xe0" + b"x" * 8


def validate(name="mou.pdf", mime="application/pdf", head=PDF_HEAD, size=1000):
    return f.validate_upload(POLICY, filename=name, declared_mime=mime, head=head, size=size)


class Validate(unittest.TestCase):
    def test_valid_types(self):
        self.assertEqual(validate().mime_type, "application/pdf")
        self.assertEqual(validate("a.PNG", "image/png", PNG_HEAD).extension, "png")
        self.assertEqual(validate("a.jpeg", "image/jpeg", JPG_HEAD).mime_type, "image/jpeg")

    def reject(self, code, **kw):
        with self.assertRaises(f.FileRejected) as ctx:
            validate(**kw)
        self.assertEqual(ctx.exception.code, code)

    def test_empty_and_too_large(self):
        self.reject("FILE_EMPTY", size=0)
        self.reject("FILE_TOO_LARGE", size=POLICY.max_bytes + 1)
        validate(size=POLICY.max_bytes)

    def test_extension_not_allowed(self):
        self.reject("FILE_TYPE_NOT_ALLOWED", name="evil.exe", mime="application/octet-stream")
        self.reject("FILE_TYPE_NOT_ALLOWED", name="noext", mime=None)

    def test_content_mismatch(self):
        self.reject("FILE_CONTENT_MISMATCH", name="fake.pdf", head=b"MZ\x90\x00" + b"x" * 12)
        self.reject("FILE_CONTENT_MISMATCH", name="a.png", mime="image/png", head=PDF_HEAD)

    def test_double_extension_checked_by_content(self):
        self.reject("FILE_CONTENT_MISMATCH", name="shell.php.pdf", head=b"<?php echo 1;")

    def test_mime_mismatch_but_octet_stream_ok(self):
        self.reject("FILE_MIME_MISMATCH", name="a.pdf", mime="image/png")
        validate(mime="application/octet-stream")
        validate(mime=None)
        validate(mime="application/pdf; charset=binary")


class FileName(unittest.TestCase):
    def test_strips_path_and_unsafe(self):
        self.assertEqual(f.sanitize_filename("../../etc/passwd.pdf"), "passwd.pdf")
        self.assertEqual(f.sanitize_filename("C:\\x\\Hợp đồng MOU (1).pdf"), "Hợp_đồng_MOU_1_.pdf")

    def test_control_chars_removed(self):
        self.assertEqual(f.sanitize_filename("a\x00b\n.pdf"), "ab.pdf")

    def test_invalid_names(self):
        for bad in ["", "   ", "...", "///", "._."]:
            with self.assertRaises(f.FileRejected):
                f.sanitize_filename(bad)

    def test_long_name_keeps_extension(self):
        out = f.sanitize_filename("a" * 500 + ".pdf")
        self.assertLessEqual(len(out), 120)
        self.assertTrue(out.endswith(".pdf"))


class ChecksumAndScan(unittest.TestCase):
    def test_sha256_streaming_equals_whole(self):
        data = b"hello world" * 1000
        chunks = [data[i : i + 333] for i in range(0, len(data), 333)]
        h1, n1 = f.sha256_of_chunks(chunks)
        h2, n2 = f.sha256_of_chunks([data])
        self.assertEqual((h1, n1), (h2, n2))
        self.assertEqual(n1, len(data))

    def test_known_digest(self):
        h, _ = f.sha256_of_chunks([b"abc"])
        self.assertEqual(h, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_checksum_matches_case_insensitive(self):
        self.assertTrue(f.checksum_matches("ABCDEF", "abcdef"))
        self.assertFalse(f.checksum_matches("abcdef", "abcdee"))

    def test_only_clean_downloadable(self):
        self.assertTrue(f.can_download(f.ScanStatus.CLEAN))
        self.assertTrue(f.can_download("CLEAN"))
        for s in (
            f.ScanStatus.PENDING,
            f.ScanStatus.QUARANTINED,
            f.ScanStatus.ERROR,
            "UNKNOWN",
            "",
            None,
        ):
            self.assertFalse(f.can_download(s), s)


if __name__ == "__main__":
    unittest.main()
