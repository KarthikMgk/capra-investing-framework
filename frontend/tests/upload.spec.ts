import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test("CSV Upload page is accessible and shows correct title", async ({ page }) => {
  await page.goto("/upload")
  await expect(page.getByRole("heading", { name: "CSV Data Upload" })).toBeVisible()
  await expect(
    page.getByText("Upload Screener.in and RBI macro data files"),
  ).toBeVisible()
})

test("Screener.in and RBI Macro Data sections are visible", async ({ page }) => {
  await page.goto("/upload")
  await expect(page.getByRole("heading", { name: "Screener.in Data" })).toBeVisible()
  await expect(page.getByRole("heading", { name: "RBI Macro Data" })).toBeVisible()
})

test("Upload buttons are disabled when no file is selected", async ({ page }) => {
  await page.goto("/upload")
  const uploadButtons = page.getByRole("button", { name: "Upload" })
  await expect(uploadButtons.first()).toBeDisabled()
  await expect(uploadButtons.last()).toBeDisabled()
})

test("File drop zones are visible", async ({ page }) => {
  await page.goto("/upload")
  const dropZones = page.getByTestId("drop-zone")
  await expect(dropZones.first()).toBeVisible()
  await expect(dropZones.last()).toBeVisible()
})

test.describe("Upload page access control", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Non-admin is redirected away from upload page", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/upload")

    await expect(page).not.toHaveURL(/\/upload/)
  })

  test("Admin can access upload page", async ({ page }) => {
    await logInUser(page, firstSuperuser, firstSuperuserPassword)

    await page.goto("/upload")

    await expect(page.getByRole("heading", { name: "CSV Data Upload" })).toBeVisible()
  })
})
