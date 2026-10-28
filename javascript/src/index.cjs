// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
exports.createClient = async function createClient() {return (await import('./node.mjs')).default;};
