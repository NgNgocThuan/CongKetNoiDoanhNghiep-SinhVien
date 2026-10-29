"""Prompt cho LLM. Người phụ trách: TV5.

Giữ prompt ở một chỗ để dễ chỉnh và review. Mọi prompt phải ép đầu ra JSON theo schema cố định,
và dùng danh mục kỹ năng của hệ thống (skills + skill_aliases) để chuẩn hóa tên.

TODO(TV5): CV_PARSE_SYSTEM, JOB_PARSE_SYSTEM, MATCH_EXPLAIN_SYSTEM (chỉ để GIẢI THÍCH, không quyết định điểm).
"""
