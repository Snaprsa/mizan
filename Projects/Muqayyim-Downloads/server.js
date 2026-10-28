/**
 * Muqaaem Local Server
 * Self-contained local workspace mode. No external API required.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 3000);
const HOST = '127.0.0.1';
const DIR = __dirname;
const APP_FILE = path.join(DIR, 'muqayyim_app.html');
const STORE_FILE = path.join(DIR, 'data', 'raw', 'muqaaem_local_store.json');

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function nowIso() {
  return new Date().toISOString();
}

function id(prefix) {
  return `${prefix}_${crypto.randomUUID()}`;
}

function parseJsonSafe(value, fallback) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function seedStore() {
  const createdAt = nowIso();
  const caseId = id('case');
  const sourceId = id('src');
  const compId = id('comp');
  return {
    meta: {
      name: 'Muqaaem',
      mode: 'local',
      created_at: createdAt,
      updated_at: createdAt,
    },
    cases: [
      {
        id: caseId,
        title: 'Riyadh Residential Demo Case',
        description: 'Local starter case for Saudi comparable review.',
        status: 'in_progress',
        created_at: createdAt,
      },
    ],
    sources: [
      {
        id: sourceId,
        case_id: caseId,
        source_type: 'url',
        status: 'fetched',
        url: 'https://sa.aqar.fm/',
        created_at: createdAt,
      },
    ],
    comparables: [
      {
        id: compId,
        case_id: caseId,
        source_id: sourceId,
        property_title: 'Sample Riyadh Apartment Comparable',
        city: 'الرياض',
        district: 'حي الصحافة',
        property_type: 'apartment',
        asking_price: 1450000,
        primary_area_sqm: 112,
        price_per_sqm: 12946,
        reliability_score: 3,
        status: 'active',
        source_url: 'https://sa.aqar.fm/',
        notes: 'Seed comparable stored locally so the app works before any live collection.',
        raw_text: 'Local sample comparable for Muqaaem offline mode.',
        created_at: createdAt,
      },
    ],
  };
}

function ensureStore() {
  ensureDir(path.dirname(STORE_FILE));
  if (!fs.existsSync(STORE_FILE)) {
    fs.writeFileSync(STORE_FILE, JSON.stringify(seedStore(), null, 2));
  }
}

function loadStore() {
  ensureStore();
  return parseJsonSafe(fs.readFileSync(STORE_FILE, 'utf8'), seedStore());
}

function saveStore(store) {
  store.meta = {
    ...(store.meta || {}),
    name: 'Muqaaem',
    mode: 'local',
    updated_at: nowIso(),
  };
  fs.writeFileSync(STORE_FILE, JSON.stringify(store, null, 2));
}

function json(res, statusCode, payload) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(JSON.stringify(payload));
}

function text(res, statusCode, body, contentType = 'text/plain; charset=utf-8', filename = null) {
  const headers = {
    'Content-Type': contentType,
    'Cache-Control': 'no-cache',
    'Access-Control-Allow-Origin': '*',
  };
  if (filename) headers['Content-Disposition'] = `attachment; filename="${filename}"`;
  res.writeHead(statusCode, headers);
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) {
        reject(new Error('Request body too large'));
      }
    });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function summarizeCase(caseItem, store) {
  const sourceCount = store.sources.filter((source) => source.case_id === caseItem.id).length;
  const comparableCount = store.comparables.filter((comp) => comp.case_id === caseItem.id).length;
  return {
    ...caseItem,
    source_count: sourceCount,
    comparable_count: comparableCount,
  };
}

function escapeCsv(value) {
  if (value === null || value === undefined) return '';
  const stringValue = String(value);
  if (/[",\n]/.test(stringValue)) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  return stringValue;
}

function domainFromUrl(value) {
  try {
    return new URL(value).hostname.replace(/^www\./, '');
  } catch {
    return 'manual';
  }
}

function cleanTitle(value) {
  return (value || '')
    .replace(/\s+/g, ' ')
    .replace(/\|.*$/, '')
    .replace(/- عقار.*$/i, '')
    .trim();
}

function firstMatch(textValue, patterns) {
  for (const pattern of patterns) {
    const match = textValue.match(pattern);
    if (match && match[1]) return match[1].trim();
  }
  return '';
}

function numberMatch(textValue, patterns) {
  const raw = firstMatch(textValue, patterns).replace(/,/g, '');
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function inferFallbackTitle(sourceUrl) {
  try {
    const pathname = new URL(sourceUrl).pathname;
    const bits = pathname.split('/').filter(Boolean);
    const last = bits[bits.length - 1] || sourceUrl;
    return decodeURIComponent(last).replace(/[-_]+/g, ' ').trim() || sourceUrl;
  } catch {
    return sourceUrl;
  }
}

async function fetchHtml(sourceUrl) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(sourceUrl, {
      signal: controller.signal,
      headers: {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
        accept: 'text/html,application/xhtml+xml',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.text();
  } finally {
    clearTimeout(timer);
  }
}

function parseComparable(source, html) {
  const title = cleanTitle(firstMatch(html, [/<title[^>]*>([^<]+)<\/title>/i])) || inferFallbackTitle(source.url);
  const askingPrice = numberMatch(html, [
    /"price"\s*:\s*"?([\d,.]+)"?/i,
    /"priceAmount"\s*:\s*"?([\d,.]+)"?/i,
    /([\d,.]+)\s*(?:ريال|sar)\b/i,
  ]);
  const area = numberMatch(html, [
    /"area"\s*:\s*"?([\d,.]+)"?/i,
    /"size"\s*:\s*"?([\d,.]+)"?/i,
    /([\d,.]+)\s*(?:م²|متر(?: مربع)?|sqm|sq\.?\s?m)/i,
  ]);
  const city = firstMatch(html, [
    /"city(?:_name)?"\s*:\s*"([^"]+)"/i,
    /"cityName"\s*:\s*"([^"]+)"/i,
    /"addressLocality"\s*:\s*"([^"]+)"/i,
  ]) || (source.url.includes('aqar') ? 'الرياض' : '');
  const district = firstMatch(html, [
    /"district(?:_name)?"\s*:\s*"([^"]+)"/i,
    /"districtName"\s*:\s*"([^"]+)"/i,
    /"streetAddress"\s*:\s*"([^"]+)"/i,
  ]);
  const propertyType = firstMatch(html, [
    /"property_type"\s*:\s*"([^"]+)"/i,
    /"category"\s*:\s*"([^"]+)"/i,
    /"@type"\s*:\s*"([^"]+)"/i,
  ]) || (source.url.includes('aqar') ? 'listing' : 'property');
  const pricePerSqm = askingPrice && area ? Math.round(askingPrice / area) : null;

  const populatedFields = [title, city, district, propertyType, askingPrice, area].filter(Boolean).length;
  const reliabilityScore = populatedFields >= 5 ? 4 : populatedFields >= 3 ? 3 : 2;

  return {
    property_title: title,
    city,
    district,
    property_type: propertyType,
    asking_price: askingPrice,
    primary_area_sqm: area,
    price_per_sqm: pricePerSqm,
    reliability_score: reliabilityScore,
    raw_text: html.slice(0, 3000),
    notes: populatedFields >= 3
      ? `Live extraction from ${domainFromUrl(source.url)} in local mode.`
      : `Stored from URL with limited field extraction in local mode.`,
  };
}

async function buildComparable(source) {
  const base = {
    id: id('comp'),
    case_id: source.case_id,
    source_id: source.id,
    property_title: inferFallbackTitle(source.url),
    city: '',
    district: '',
    property_type: source.url.includes('aqar') ? 'listing' : 'property',
    asking_price: null,
    primary_area_sqm: null,
    price_per_sqm: null,
    reliability_score: 2,
    status: 'active',
    source_url: source.url,
    notes: 'Saved in local mode without a remote backend.',
    raw_text: '',
    created_at: nowIso(),
  };

  try {
    const html = await fetchHtml(source.url);
    return { ...base, ...parseComparable(source, html) };
  } catch (error) {
    return {
      ...base,
      notes: `Fallback local extraction used. ${error.message}`,
      raw_text: '',
    };
  }
}

function buildCsv(comparables) {
  const header = [
    'property_title',
    'city',
    'district',
    'property_type',
    'asking_price',
    'primary_area_sqm',
    'price_per_sqm',
    'reliability_score',
    'status',
    'source_url',
    'notes',
  ];
  const rows = comparables.map((comp) => header.map((column) => escapeCsv(comp[column])));
  return [header.join(','), ...rows.map((row) => row.join(','))].join('\n');
}

function buildHtmlReport(caseItem, comparables) {
  const rows = comparables.map((comp) => `
    <tr>
      <td>${comp.property_title || '—'}</td>
      <td>${comp.city || '—'}</td>
      <td>${comp.district || '—'}</td>
      <td>${comp.property_type || '—'}</td>
      <td>${comp.asking_price ? Number(comp.asking_price).toLocaleString('en-SA') : '—'}</td>
      <td>${comp.primary_area_sqm ? Number(comp.primary_area_sqm).toLocaleString('en-SA') : '—'}</td>
      <td>${comp.price_per_sqm ? Number(comp.price_per_sqm).toLocaleString('en-SA') : '—'}</td>
      <td>${comp.notes || '—'}</td>
    </tr>
  `).join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${caseItem.title} - Muqaaem Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 32px; color: #0f172a; }
    h1 { margin: 0 0 8px; }
    p { color: #475569; }
    table { width: 100%; border-collapse: collapse; margin-top: 24px; font-size: 14px; }
    th, td { border: 1px solid #cbd5e1; padding: 10px 12px; text-align: left; vertical-align: top; }
    th { background: #f8fafc; }
  </style>
</head>
<body>
  <h1>${caseItem.title}</h1>
  <p>${caseItem.description || 'Local Muqaaem export report.'}</p>
  <p>Generated ${new Date().toLocaleString('en-SA')}</p>
  <table>
    <thead>
      <tr>
        <th>Property</th>
        <th>City</th>
        <th>District</th>
        <th>Type</th>
        <th>Price</th>
        <th>Area</th>
        <th>SAR/m²</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>${rows || '<tr><td colspan="8">No comparables yet.</td></tr>'}</tbody>
  </table>
</body>
</html>`;
}

function notFound(res) {
  json(res, 404, { detail: 'Not found' });
}

async function handleApi(req, res, pathname) {
  const store = loadStore();
  const segments = pathname.split('/').filter(Boolean);

  if (pathname === '/api/health' && req.method === 'GET') {
    json(res, 200, {
      status: 'ok',
      version: 'local',
      mode: 'local',
      name: 'Muqaaem',
      counts: {
        cases: store.cases.length,
        sources: store.sources.length,
        comparables: store.comparables.length,
      },
    });
    return;
  }

  if (pathname === '/api/v1/cases' && req.method === 'GET') {
    const cases = [...store.cases]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .map((item) => summarizeCase(item, store));
    json(res, 200, { data: cases, total: cases.length });
    return;
  }

  if (pathname === '/api/v1/cases' && req.method === 'POST') {
    const body = parseJsonSafe(await readBody(req), {});
    const title = String(body.title || '').trim();
    if (!title) {
      json(res, 400, { detail: 'Case title is required.' });
      return;
    }
    const newCase = {
      id: id('case'),
      title,
      description: String(body.description || '').trim(),
      status: 'draft',
      created_at: nowIso(),
    };
    store.cases.push(newCase);
    saveStore(store);
    json(res, 201, summarizeCase(newCase, store));
    return;
  }

  if (segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[3] && !segments[4] && req.method === 'GET') {
    const caseItem = store.cases.find((item) => item.id === segments[3]);
    if (!caseItem) {
      notFound(res);
      return;
    }
    json(res, 200, summarizeCase(caseItem, store));
    return;
  }

  if (segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[3] && segments[4] === 'sources' && !segments[5] && req.method === 'GET') {
    const sources = store.sources
      .filter((item) => item.case_id === segments[3])
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    json(res, 200, sources);
    return;
  }

  if (segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[3] && segments[4] === 'sources' && segments[5] === 'url' && req.method === 'POST') {
    const caseExists = store.cases.some((item) => item.id === segments[3]);
    if (!caseExists) {
      notFound(res);
      return;
    }
    const body = parseJsonSafe(await readBody(req), {});
    const sourceUrl = String(body.url || '').trim();
    if (!sourceUrl) {
      json(res, 400, { detail: 'URL is required.' });
      return;
    }
    const source = {
      id: id('src'),
      case_id: segments[3],
      source_type: 'url',
      status: 'pending',
      url: sourceUrl,
      domain: domainFromUrl(sourceUrl),
      created_at: nowIso(),
    };
    store.sources.push(source);
    saveStore(store);
    json(res, 201, source);
    return;
  }

  if (segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'sources' && segments[3] && segments[4] === 'extract' && req.method === 'POST') {
    const source = store.sources.find((item) => item.id === segments[3]);
    if (!source) {
      notFound(res);
      return;
    }
    source.status = 'fetching';
    saveStore(store);

    const comparable = await buildComparable(source);
    const existingIndex = store.comparables.findIndex((item) => item.source_id === source.id);
    if (existingIndex >= 0) {
      store.comparables[existingIndex] = {
        ...store.comparables[existingIndex],
        ...comparable,
      };
    } else {
      store.comparables.push(comparable);
    }
    source.status = 'fetched';

    const caseItem = store.cases.find((item) => item.id === source.case_id);
    if (caseItem && caseItem.status === 'draft') {
      caseItem.status = 'in_progress';
    }
    saveStore(store);
    json(res, 200, { status: 'completed', job_id: comparable.id, comparable_id: comparable.id });
    return;
  }

  if (segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[3] && segments[4] === 'comparables' && req.method === 'GET') {
    const comparables = store.comparables
      .filter((item) => item.case_id === segments[3])
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    json(res, 200, { data: comparables, total: comparables.length });
    return;
  }

  if (segments[0] === 'api' && segments[1] === 'v1' && segments[2] === 'cases' && segments[3] && segments[4] === 'export' && segments[5] && req.method === 'GET') {
    const caseItem = store.cases.find((item) => item.id === segments[3]);
    if (!caseItem) {
      notFound(res);
      return;
    }
    const comparables = store.comparables.filter((item) => item.case_id === caseItem.id);
    if (segments[5] === 'csv') {
      text(res, 200, buildCsv(comparables), 'text/csv; charset=utf-8', 'muqaaem-comparables.csv');
      return;
    }
    if (segments[5] === 'json') {
      text(
        res,
        200,
        JSON.stringify({ case: summarizeCase(caseItem, store), comparables }, null, 2),
        'application/json; charset=utf-8',
        'muqaaem-comparables.json'
      );
      return;
    }
    if (segments[5] === 'html') {
      text(res, 200, buildHtmlReport(caseItem, comparables), 'text/html; charset=utf-8', 'muqaaem-report.html');
      return;
    }
    notFound(res);
    return;
  }

  notFound(res);
}

function serveStatic(res, pathname) {
  const filePath = path.join(DIR, pathname === '/' ? 'muqayyim_app.html' : pathname.replace(/^\/+/, ''));
  const ext = path.extname(filePath);
  const mime = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.json': 'application/json; charset=utf-8',
    '.csv': 'text/csv; charset=utf-8',
  };

  fs.readFile(filePath, (error, data) => {
    if (error) {
      fs.readFile(APP_FILE, (fallbackError, fallbackData) => {
        if (fallbackError) {
          text(res, 500, 'App file missing');
          return;
        }
        text(res, 200, fallbackData, 'text/html; charset=utf-8');
      });
      return;
    }

    text(res, 200, data, mime[ext] || 'text/plain; charset=utf-8');
  });
}

ensureStore();

http.createServer(async (req, res) => {
  try {
    const requestUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const pathname = requestUrl.pathname;

    if (req.method === 'OPTIONS') {
      res.writeHead(204, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      });
      res.end();
      return;
    }

    if (pathname.startsWith('/api/')) {
      await handleApi(req, res, pathname);
      return;
    }

    serveStatic(res, pathname);
  } catch (error) {
    console.error(error);
    json(res, 500, { detail: error.message || 'Server error' });
  }
}).listen(PORT, HOST, () => {
  console.log(`Muqaaem running at http://localhost:${PORT}`);
  console.log(`Local store: ${STORE_FILE}`);
});
