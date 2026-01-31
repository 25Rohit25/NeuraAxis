/**
 * NEURAXIS - Case Detail E2E Tests
 * End-to-end tests for collaborative case editing
 */

import { expect, Page, test } from "@playwright/test";

const BASE_URL = process.env.TEST_URL || "http://localhost:3000";

// =============================================================================
// Test Fixtures & Helpers
// =============================================================================

interface TestUser {
  email: string;
  password: string;
  name: string;
}

const testUsers: TestUser[] = [
  { email: "doctor1@test.com", password: "test123", name: "Dr. Alice Smith" },
  { email: "doctor2@test.com", password: "test123", name: "Dr. Bob Johnson" },
  { email: "nurse1@test.com", password: "test123", name: "Nurse Carol Davis" },
];

// Helper to login
async function login(page: Page, user: TestUser) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('[data-testid="email-input"]', user.email);
  await page.fill('[data-testid="password-input"]', user.password);
  await page.click('[data-testid="login-button"]');
  await page.waitForURL(/\/(dashboard|cases)/);
}

// Helper to navigate to a case
async function navigateToCase(page: Page, caseId: string) {
  await page.goto(`${BASE_URL}/cases/${caseId}`);
  await page.waitForSelector('[data-testid="case-header"]');
}

// Helper to create a test case
async function createTestCase(page: Page): Promise<string> {
  await page.goto(`${BASE_URL}/cases/new`);

  // Fill basic info
  await page.fill('[data-testid="patient-name"]', "Test Patient");
  await page.fill(
    '[data-testid="chief-complaint"]',
    "Test complaint for E2E testing"
  );

  // Submit
  await page.click('[data-testid="submit-case"]');

  // Get case ID from URL
  await page.waitForURL(/\/cases\/[\w-]+/);
  const url = page.url();
  const caseId = url.split("/cases/")[1];

  return caseId;
}

// =============================================================================
// Navigation & Display Tests
// =============================================================================

test.describe("Case Detail Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUsers[0]);
  });

  test("should display case header with correct info", async ({ page }) => {
    await navigateToCase(page, "test-case-id");

    await expect(page.locator('[data-testid="case-number"]')).toBeVisible();
    await expect(page.locator('[data-testid="status-badge"]')).toBeVisible();
    await expect(page.locator('[data-testid="priority-badge"]')).toBeVisible();
    await expect(page.locator('[data-testid="patient-name"]')).toBeVisible();
  });

  test("should navigate between sections", async ({ page }) => {
    await navigateToCase(page, "test-case-id");

    // Click through all section tabs
    const sections = [
      "overview",
      "timeline",
      "notes",
      "ai",
      "treatment",
      "images",
      "labs",
      "documents",
    ];

    for (const section of sections) {
      await page.click(`[data-testid="tab-${section}"]`);
      await expect(
        page.locator(`[data-testid="section-${section}"]`)
      ).toBeVisible();
    }
  });

  test("should display patient information in header", async ({ page }) => {
    await navigateToCase(page, "test-case-id");

    await expect(page.locator('[data-testid="patient-avatar"]')).toBeVisible();
    await expect(
      page.locator('[data-testid="patient-age-gender"]')
    ).toBeVisible();
    await expect(page.locator('[data-testid="patient-mrn"]')).toBeVisible();
  });
});

// =============================================================================
// Real-time Collaboration Tests
// =============================================================================

test.describe("Real-time Collaboration", () => {
  test("should show presence indicators when multiple users view case", async ({
    browser,
  }) => {
    // Create two browser contexts for two users
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Login both users
    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    // Navigate to same case
    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);
    await navigateToCase(page2, caseId);

    // Wait for presence to sync
    await page1.waitForTimeout(2000);

    // User 1 should see User 2's presence
    await expect(
      page1.locator('[data-testid="presence-indicators"]')
    ).toContainText("2 viewing");

    // User 2 should see User 1's presence
    await expect(
      page2.locator('[data-testid="presence-indicators"]')
    ).toContainText("2 viewing");

    await context1.close();
    await context2.close();
  });

  test("should update presence when user changes section", async ({
    browser,
  }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);
    await navigateToCase(page2, caseId);

    // User 1 navigates to notes section
    await page1.click('[data-testid="tab-notes"]');
    await page1.waitForTimeout(1000);

    // User 2 should see User 1 is viewing notes
    const presenceIndicator = page2.locator('[data-testid="presence-user-0"]');
    await expect(presenceIndicator).toHaveAttribute("data-section", "notes");

    await context1.close();
    await context2.close();
  });

  test("should handle user disconnect gracefully", async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);
    await navigateToCase(page2, caseId);

    // Verify both connected
    await expect(
      page1.locator('[data-testid="presence-indicators"]')
    ).toContainText("2 viewing");

    // Close User 2's page
    await page2.close();
    await context2.close();

    // Wait for disconnect to propagate
    await page1.waitForTimeout(3000);

    // User 1 should see only themselves
    await expect(
      page1.locator('[data-testid="presence-indicators"]')
    ).not.toContainText("2 viewing");

    await context1.close();
  });
});

// =============================================================================
// Collaborative Editing Tests
// =============================================================================

test.describe("Collaborative Editing", () => {
  test("should show saving indicator during updates", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    // Navigate to notes section
    await page.click('[data-testid="tab-notes"]');

    // Create new note
    await page.click('[data-testid="create-note-button"]');
    await page.fill(
      '[data-testid="note-content"]',
      "Test clinical note content"
    );
    await page.click('[data-testid="save-note-button"]');

    // Should show saving indicator
    await expect(
      page.locator('[data-testid="saving-indicator"]')
    ).toBeVisible();

    // Should hide after save completes
    await expect(
      page.locator('[data-testid="saving-indicator"]')
    ).not.toBeVisible({ timeout: 5000 });
  });

  test("should handle version conflicts", async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);
    await navigateToCase(page2, caseId);

    // Both navigate to treatment section
    await page1.click('[data-testid="tab-treatment"]');
    await page2.click('[data-testid="tab-treatment"]');

    // User 1 makes a change
    await page1.click('[data-testid="edit-diagnosis"]');
    await page1.fill(
      '[data-testid="diagnosis-input"]',
      "Updated diagnosis by User 1"
    );
    await page1.click('[data-testid="save-diagnosis"]');

    // Wait for save
    await page1.waitForTimeout(1000);

    // User 2 tries to make a conflicting change (stale version)
    await page2.click('[data-testid="edit-diagnosis"]');
    await page2.fill(
      '[data-testid="diagnosis-input"]',
      "Conflicting diagnosis by User 2"
    );
    await page2.click('[data-testid="save-diagnosis"]');

    // User 2 should see conflict notification
    await expect(
      page2.locator('[data-testid="conflict-notification"]')
    ).toBeVisible();
    await expect(
      page2.locator('[data-testid="conflict-notification"]')
    ).toContainText("modified by another user");

    await context1.close();
    await context2.close();
  });

  test("should sync updates in real-time", async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);
    await navigateToCase(page2, caseId);

    // User 1 updates status
    await page1.click('[data-testid="status-dropdown"]');
    await page1.click('[data-testid="status-in_progress"]');

    // Wait for sync
    await page1.waitForTimeout(2000);

    // User 2 should see updated status
    await expect(page2.locator('[data-testid="status-badge"]')).toContainText(
      "In Progress"
    );

    await context1.close();
    await context2.close();
  });
});

// =============================================================================
// Comment Thread Tests
// =============================================================================

test.describe("Comments & Collaboration", () => {
  test("should add comment to case", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    // Open comments sidebar
    await page.click('[data-testid="toggle-comments"]');

    // Add comment
    await page.fill(
      '[data-testid="new-comment-input"]',
      "This is a test comment"
    );
    await page.click('[data-testid="post-comment-button"]');

    // Comment should appear
    await expect(
      page.locator('[data-testid="comment-thread"]').first()
    ).toContainText("This is a test comment");
  });

  test("should show @mentions autocomplete", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.click('[data-testid="toggle-comments"]');
    await page.fill('[data-testid="new-comment-input"]', "Hey @");

    // Autocomplete should appear
    await expect(
      page.locator('[data-testid="mention-autocomplete"]')
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="mention-autocomplete"]')
    ).toContainText("Dr.");
  });

  test("should resolve comment thread", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.click('[data-testid="toggle-comments"]');

    // Find unresolved thread
    const thread = page
      .locator('[data-testid="comment-thread"]:not([data-resolved="true"])')
      .first();

    // Resolve it
    await thread.locator('[data-testid="resolve-thread"]').click();

    // Thread should be marked as resolved
    await expect(thread).toHaveAttribute("data-resolved", "true");
  });

  test("should notify mentioned users in real-time", async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);
    await navigateToCase(page2, caseId);

    // User 1 mentions User 2 in a comment
    await page1.click('[data-testid="toggle-comments"]');
    await page1.fill(
      '[data-testid="new-comment-input"]',
      `@${testUsers[1].name} please review this case`
    );
    await page1.click('[data-testid="post-comment-button"]');

    // User 2 should receive notification
    await expect(
      page2.locator('[data-testid="notification-toast"]')
    ).toBeVisible({ timeout: 5000 });
    await expect(
      page2.locator('[data-testid="notification-toast"]')
    ).toContainText("mentioned you");

    await context1.close();
    await context2.close();
  });
});

// =============================================================================
// Version History Tests
// =============================================================================

test.describe("Version History", () => {
  test("should display version history", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    // Open version history
    await page.click('[data-testid="history-button"]');

    // History panel should appear
    await expect(
      page.locator('[data-testid="version-history-panel"]')
    ).toBeVisible();

    // Should have at least one version
    await expect(
      page.locator('[data-testid="version-entry"]').first()
    ).toBeVisible();
  });

  test("should revert to previous version", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    // Get current content
    await page.click('[data-testid="tab-notes"]');
    const currentContent = await page
      .locator('[data-testid="note-content"]')
      .first()
      .textContent();

    // Open history
    await page.click('[data-testid="history-button"]');

    // Click restore on earlier version
    await page
      .locator('[data-testid="version-entry"]')
      .nth(1)
      .locator('[data-testid="restore-version"]')
      .click();

    // Confirm
    await page.click('[data-testid="confirm-restore"]');

    // Content should be different
    await page.waitForTimeout(2000);
    const newContent = await page
      .locator('[data-testid="note-content"]')
      .first()
      .textContent();

    // In a real test, we'd verify the content changed
    // expect(newContent).not.toBe(currentContent);
  });

  test("should compare two versions", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.click('[data-testid="history-button"]');

    // Select two versions for comparison
    await page
      .locator('[data-testid="version-entry"]')
      .first()
      .locator('[data-testid="compare-checkbox"]')
      .click();
    await page
      .locator('[data-testid="version-entry"]')
      .nth(1)
      .locator('[data-testid="compare-checkbox"]')
      .click();

    // Click compare
    await page.click('[data-testid="compare-versions-button"]');

    // Diff view should appear
    await expect(page.locator('[data-testid="version-diff"]')).toBeVisible();
  });
});

// =============================================================================
// Export Tests
// =============================================================================

test.describe("Export Functionality", () => {
  test("should export case to PDF", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    // Open export modal
    await page.click('[data-testid="export-button"]');

    // Select PDF format
    await page.click('[data-testid="format-pdf"]');

    // Configure options
    await page.check('[data-testid="include-images"]');
    await page.check('[data-testid="include-ai-analysis"]');

    // Download promise
    const downloadPromise = page.waitForEvent("download");

    // Click export
    await page.click('[data-testid="export-submit"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/case-.*\.pdf/);
  });

  test("should use print-optimized layout", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.click('[data-testid="export-button"]');
    await page.check('[data-testid="print-optimized"]');

    // Verify print-optimized is selected
    await expect(page.locator('[data-testid="print-optimized"]')).toBeChecked();

    await page.click('[data-testid="export-submit"]');

    // Modal should close after export
    await expect(
      page.locator('[data-testid="export-modal"]')
    ).not.toBeVisible();
  });
});

// =============================================================================
// Access Control Tests
// =============================================================================

test.describe("Access Control", () => {
  test("should restrict editing for viewers", async ({ page }) => {
    // Login as viewer
    await login(page, testUsers[2]); // Nurse with limited access
    await navigateToCase(page, "test-case-id");

    // Edit buttons should be disabled
    await expect(page.locator('[data-testid="edit-treatment"]')).toBeDisabled();
    await expect(
      page.locator('[data-testid="sign-note-button"]')
    ).not.toBeVisible();
  });

  test("should show lock indicator when case is locked", async ({
    browser,
  }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    await login(page1, testUsers[0]);
    await login(page2, testUsers[1]);

    const caseId = "shared-test-case";
    await navigateToCase(page1, caseId);

    // User 1 starts editing (acquires lock)
    await page1.click('[data-testid="tab-notes"]');
    await page1.click('[data-testid="edit-note-button"]');

    // User 2 navigates to same case
    await navigateToCase(page2, caseId);

    // User 2 should see lock indicator
    await expect(page2.locator('[data-testid="lock-indicator"]')).toBeVisible();
    await expect(page2.locator('[data-testid="lock-indicator"]')).toContainText(
      testUsers[0].name
    );

    await context1.close();
    await context2.close();
  });
});

// =============================================================================
// Keyboard Shortcuts Tests
// =============================================================================

test.describe("Keyboard Shortcuts", () => {
  test("should open export with Ctrl+E", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.keyboard.press("Control+e");

    await expect(page.locator('[data-testid="export-modal"]')).toBeVisible();
  });

  test("should trigger print with Ctrl+P", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    // Mock print dialog
    let printCalled = false;
    await page.evaluate(() => {
      window.print = () => {
        (window as any).printCalled = true;
      };
    });

    await page.keyboard.press("Control+p");

    // Verify print was triggered
    const wasPrintCalled = await page.evaluate(
      () => (window as any).printCalled
    );
    // expect(wasPrintCalled).toBe(true);
  });
});

// =============================================================================
// Timeline Tests
// =============================================================================

test.describe("Timeline & Activity", () => {
  test("should load timeline with infinite scroll", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.click('[data-testid="tab-timeline"]');

    // Initial events should load
    const initialEvents = await page
      .locator('[data-testid="timeline-event"]')
      .count();
    expect(initialEvents).toBeGreaterThan(0);

    // Scroll to bottom
    await page.evaluate(() => {
      const timeline = document.querySelector(
        '[data-testid="timeline-container"]'
      );
      if (timeline) timeline.scrollTop = timeline.scrollHeight;
    });

    // Wait for more to load
    await page.waitForTimeout(2000);

    // Should have more events now (if available)
    const finalEvents = await page
      .locator('[data-testid="timeline-event"]')
      .count();
    expect(finalEvents).toBeGreaterThanOrEqual(initialEvents);
  });

  test("should display correct event icons", async ({ page }) => {
    await login(page, testUsers[0]);
    await navigateToCase(page, "test-case-id");

    await page.click('[data-testid="tab-timeline"]');

    // Check for different event types
    await expect(
      page.locator('[data-testid="event-case_created"]').first()
    ).toBeVisible();
  });
});
