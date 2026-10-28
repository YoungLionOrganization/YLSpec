// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import ylspec = require('@younglionorganization/ylspec');
async function example() {const yl = await ylspec.createClient(); const bytes: Uint8Array = yl.pack(new yl.Document({count: 42n})); return bytes;}
void example;
