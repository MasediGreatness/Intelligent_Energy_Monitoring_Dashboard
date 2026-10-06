import process from 'node:process'

import { defineConfig } from '@playwright/test'

const evidenceStep = process.env.E2E_EVIDENCE_STEP ?? '14'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  outputDir: `../../docs/test-evidence/step-${evidenceStep}-playwright-artifacts`,
  reporter: [
    ['list'],
    [
      'junit',
      {
        outputFile: `../../docs/test-evidence/step-${evidenceStep}-playwright-junit.xml`,
      },
    ],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
})
