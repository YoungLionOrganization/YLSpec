// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const {execFileSync} = require('node:child_process');
const {mkdirSync} = require('node:fs');
const path = require('node:path');
const {version} = require('../package.json');
const output = path.resolve(__dirname, '../../../dist/editor');
mkdirSync(output, {recursive: true});
execFileSync(process.execPath, [require.resolve('@vscode/vsce/vsce'), 'package', '--no-dependencies', '--out', path.join(output, `ylspec-${version}.vsix`)], {stdio: 'inherit'});
