// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {test, expect} from '@playwright/test';
test('React initializes the real WebAssembly C core', async ({page}) => {
  page.on('pageerror', error => console.error(error));
  page.on('console', message => {if (message.type() === 'error') console.error(message.text());});
  await page.goto('/test/browser.html'); await expect(page.locator('output')).toHaveText('React browser');
  const result = await page.evaluate(async () => {
    const {createClient} = await import('/src/web.mjs'); const yl = await createClient();
    const doc = new yl.Document({integer: 9223372036854775807n, stamp: new yl.TemporalValue('datetime-offset', '2026-10-28T12:34:56.123456789Z')});
    const restored = yl.unpack(yl.pack(doc)); return [yl.backend, String(restored.data.integer), restored.data.stamp.text];
  });
  expect(result).toEqual(['wasm', '9223372036854775807', '2026-10-28T12:34:56.123456789Z']);
});
