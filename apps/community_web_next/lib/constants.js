export const USER_ROLE = {
  admin: "ADMIN",
  internal: "INTERNAL",
  user: "USER",
  visitor: "VISITOR",
};

export const REGEX = {
  koreanCharacters:
    /[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]$/i,
  usernameFirstCharacter:
    /^[A-Za-z]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]/i,
  usernameFull:
    /^([A-Za-z0-9_.]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff])+$/i,
};
