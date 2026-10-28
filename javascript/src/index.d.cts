/** Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
 * CommonJS shares the same asynchronous factory and native client contract.
 */
import type {Client, ClientOptions} from './index.js' with {'resolution-mode': 'import'};
export function createClient(options?: ClientOptions): Promise<Client>;
