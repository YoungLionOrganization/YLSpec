// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {createClient, type Document} from '@younglionorganization/ylspec';
async function example(): Promise<Document> {
  const yl = await createClient(); const doc = new yl.Document({name: 'typed', count: 42n});
  const bytes: Uint8Array = yl.pack(doc); return yl.unpack(bytes);
}
void example;
