// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {defineConfig} from '@playwright/test';
export default defineConfig({testDir: '.', testMatch: 'browser.spec.mjs', use: {baseURL: 'http://127.0.0.1:4173'}, webServer: {command: 'npx vite --host 127.0.0.1 --port 4173', url: 'http://127.0.0.1:4173/test/browser.html', reuseExistingServer: false}});
