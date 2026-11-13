export const projectCategories: [string, string][] = [
  ["DEVELOPMENT", "Lập trình & công nghệ"],
  ["DESIGN", "Thiết kế"],
  ["CONTENT", "Nội dung & biên tập"],
  ["MARKETING", "Marketing"],
  ["DATA", "Dữ liệu & nghiên cứu"],
  ["TRANSLATION", "Biên phiên dịch"],
  ["OTHER", "Khác"],
];
export const projectExperience: [string, string][] = [
  ["ENTRY", "Cơ bản / mới bắt đầu"],
  ["INTERMEDIATE", "Đã có kinh nghiệm"],
  ["ADVANCED", "Chuyên sâu"],
];
export const projectOptionLabel = (
  options: [string, string][],
  value: unknown,
) => options.find(([key]) => key === value)?.[1] ?? "Chưa chọn";
