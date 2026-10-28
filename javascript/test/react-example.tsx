// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {useEffect, useState} from 'react';
import {createClient} from '../src/web.mjs';
export function MetadataView() {
  const [name, setName] = useState('Loading');
  useEffect(() => {let active = true; void createClient().then(yl => {const doc = new yl.Document({name: 'React browser'}); if (active) setName(String(yl.unpack(yl.pack(doc)).data.name));}).catch(() => {if (active) setName('Unable to initialize metadata');}); return () => {active = false;};}, []);
  return <output aria-live="polite">{name}</output>;
}
