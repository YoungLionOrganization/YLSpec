// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const path = require('node:path');
const {runTests} = require('@vscode/test-electron');
runTests({extensionDevelopmentPath: path.resolve(__dirname, '..'), extensionTestsPath: path.resolve(__dirname, 'suite.cjs'), launchArgs: ['--no-sandbox', '--disable-gpu', '--disable-extensions', '--skip-welcome', '--skip-release-notes']}).catch(error => {console.error(error); process.exitCode = 1;});
