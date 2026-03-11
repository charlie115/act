import { USER_ROLE } from "./constants";

export const POST_CATEGORY_LIST = [
  { value: "Announcement", color: "#c2410c" },
  { value: "Freewriting", color: "#7c3aed" },
  { value: "Question", color: "#0a7e6a" },
  { value: "Investment Strategy", color: "#0f766e" },
  { value: "Information", color: "#0284c7" },
  { value: "User Guide", color: "#0891b2" },
];

export function getAllowedBoardCategories(user) {
  if (!user) {
    return POST_CATEGORY_LIST.filter(
      (item) => item.value !== "Announcement" && item.value !== "User Guide"
    );
  }

  if (user.role === USER_ROLE.admin || user.role === USER_ROLE.internal) {
    return POST_CATEGORY_LIST;
  }

  return POST_CATEGORY_LIST.filter(
    (item) => item.value !== "Announcement" && item.value !== "User Guide"
  );
}
