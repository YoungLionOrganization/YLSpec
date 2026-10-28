// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
/** Initialize the synchronous native Node client behind the shared async factory. */
export async function createClient() {return (await import('./node.mjs')).default;}
