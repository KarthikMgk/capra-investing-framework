import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test("Kite Settings page shows correct title", async ({ page }) => {
  await page.goto("/admin/settings")
  await expect(
    page.getByRole("heading", { name: "Kite Connect Settings" }),
  ).toBeVisible()
})

test("API Key and Access Token fields are visible", async ({ page }) => {
  await page.goto("/admin/settings")
  await expect(page.getByLabel("API Key")).toBeVisible()
  await expect(page.getByLabel("Access Token")).toBeVisible()
})

test("Save Credentials button is visible", async ({ page }) => {
  await page.goto("/admin/settings")
  await expect(
    page.getByRole("button", { name: "Save Credentials" }),
  ).toBeVisible()
})

test("Saving valid credentials shows success message", async ({ page }) => {
  await page.goto("/admin/settings")

  await page.getByLabel("API Key").fill("test-api-key-12345")
  await page.getByLabel("Access Token").fill("test-access-token-12345")
  await page.getByRole("button", { name: "Save Credentials" }).click()

  await expect(page.getByText("Credentials saved successfully")).toBeVisible()
})

test("Cancel button appears when form is dirty and resets the form", async ({
  page,
}) => {
  await page.goto("/admin/settings")

  await page.getByLabel("API Key").fill("some-api-key")

  await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible()

  await page.getByRole("button", { name: "Cancel" }).click()

  await expect(page.getByLabel("API Key")).toHaveValue("")
  await expect(page.getByRole("button", { name: "Cancel" })).not.toBeVisible()
})

test("API Key is required", async ({ page }) => {
  await page.goto("/admin/settings")

  await page.getByLabel("Access Token").fill("some-token")
  await page.getByRole("button", { name: "Save Credentials" }).click()

  await expect(page.getByText("API Key is required")).toBeVisible()
})

test("Access Token is required", async ({ page }) => {
  await page.goto("/admin/settings")

  await page.getByLabel("API Key").fill("some-key")
  await page.getByRole("button", { name: "Save Credentials" }).click()

  await expect(page.getByText("Access Token is required")).toBeVisible()
})

test.describe("Kite Settings access control", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Non-admin is redirected away from kite settings", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/admin/settings")

    await expect(page).not.toHaveURL(/\/admin\/settings/)
  })

  test("Admin can access kite settings", async ({ page }) => {
    await logInUser(page, firstSuperuser, firstSuperuserPassword)

    await page.goto("/admin/settings")

    await expect(
      page.getByRole("heading", { name: "Kite Connect Settings" }),
    ).toBeVisible()
  })
})
