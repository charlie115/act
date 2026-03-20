"use server";

import { generateApiToken } from "../apiToken.server";

export async function refreshApiToken() {
  return generateApiToken();
}
