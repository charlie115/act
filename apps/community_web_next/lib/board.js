import { USER_ROLE } from "./constants";

export const POST_CATEGORY_LIST = [
  { value: "Announcement", color: "#c2410c", getLabel: () => "Announcement" },
  { value: "Freewriting", color: "#7c3aed", getLabel: () => "Freewriting" },
  { value: "Question", color: "#0a7e6a", getLabel: () => "Question" },
  {
    value: "Investment Strategy",
    color: "#0f766e",
    getLabel: () => "Investment Strategy",
  },
  { value: "Information", color: "#0284c7", getLabel: () => "Information" },
  { value: "User Guide", color: "#0891b2", getLabel: () => "User Guide" },
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
