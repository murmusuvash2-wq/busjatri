// scripts/test_search_flow.js
// Comprehensive test suite for search flow in BusJatri

const fs = require('fs');
const path = require('path');

// Set up browser-like environment
global.window = {
  addEventListener: () => {},
  scrollTo: () => {},
  location: { hash: '#/' },
  localStorage: { getItem: () => null, setItem: () => {} },
  matchMedia: () => ({ matches: false }),
  __BJ_SEARCH_CACHE: {},
  __BJ_SEARCH_SCROLL: {}
};
global.MutationObserver = class {
  constructor() {}
  observe() {}
  disconnect() {}
};
global.document = {
  addEventListener: () => {},
  querySelectorAll: () => [],
  querySelector: () => null,
  getElementById: (id) => ({
    id,
    value: '',
    innerHTML: '',
    appendChild: () => {},
    classList: { add: () => {}, remove: () => {} },
    scrollIntoView: () => {}
  }),
  documentElement: { setAttribute: () => {} },
  body: { classList: { toggle: () => {} } }
};
global.location = global.window.location;
global.localStorage = global.window.localStorage;
global.navigator = { serviceWorker: { register: () => Promise.resolve() } };

// Mock fetch to load local JSON files
global.fetch = async (url) => {
  const cleanUrl = url.replace(/^\//, '');
  const filePath = path.join(__dirname, '..', cleanUrl);
  if (fs.existsSync(filePath)) {
    const data = fs.readFileSync(filePath, 'utf8');
    return {
      ok: true,
      status: 200,
      json: async () => JSON.parse(data),
      text: async () => data
    };
  }
  throw new Error(`File not found: ${url} (${filePath})`);
};

// Evaluate scripts in order
const rootDir = path.join(__dirname, '..');
const appJs = fs.readFileSync(path.join(rootDir, 'js', 'app.js'), 'utf8');
const uxFixesJs = fs.readFileSync(path.join(rootDir, 'js', 'ux-fixes.js'), 'utf8');
const stopSearchJs = fs.readFileSync(path.join(rootDir, 'js', 'stop-search-all.js'), 'utf8');
const altRouteJs = fs.readFileSync(path.join(rootDir, 'js', 'alt-route.js'), 'utf8');

const vm = require('vm');
const patchVars = (code) => code.replace(/^let (DATA|BUSES|ROUTES|STOPS|FULL_BUSES|LANG|SN|TOP_ROUTES|FULL_PROMISE)/m, 'var $1');
vm.runInThisContext(patchVars(appJs));
vm.runInThisContext(uxFixesJs);
vm.runInThisContext(stopSearchJs);
vm.runInThisContext(altRouteJs);

async function runTests() {
  console.log('Loading app data...');
  await ensureFullData();
  console.log(`Loaded ${Object.keys(BUSES).length} buses.`);

  const testCases = [
    { name: 'Route search: Bankura to Digha', hash: '#/search?from=Bankura&to=Digha', minResults: 1 },
    { name: 'Route search: Kolkata to Durgapur', hash: '#/search?from=Kolkata&to=Durgapur', minResults: 1 },
    { name: 'Route search: Siliguri to Cooch Behar', hash: '#/search?from=Siliguri&to=Cooch+Behar', minResults: 1 },
    { name: 'Stop search: Kolaghat', hash: '#/search?stop=Kolaghat', minResults: 1 },
    { name: 'Stop search: Santuri', hash: '#/search?stop=Santuri', minResults: 1, maxResults: 50 },
    { name: 'Single place search: Bankura', hash: '#/search?from=Bankura', minResults: 1 },
    { name: 'Time query: 8:00 AM', hash: '#/search?from=8:00+AM', minResults: 1 },
    { name: 'Operator filter: SBSTC', hash: '#/search?op=sbstc', minResults: 1 },
    { name: 'Empty / No route', hash: '#/search?from=Nowhere1234&to=Somewhere9999', minResults: 0, maxResults: 0 },
    { name: 'Alt route query: Khatra to Durgapur (1-change)', hash: '#/search?from=Khatra&to=Durgapur', checkAlt: true }
  ];

  let passed = 0;
  let failed = 0;

  for (const tc of testCases) {
    location.hash = tc.hash;
    let containerObj = {
      innerHTML: '',
      insertAdjacentHTML: function (pos, str) {
        mockEl.innerHTML += str;
      },
      querySelector: function (sel) {
        if (sel === '.empty-state' && mockEl.innerHTML.includes('empty-state')) {
          return {
            insertAdjacentHTML: (pos, str) => { mockEl.innerHTML += str; }
          };
        }
        return null;
      }
    };
    let mockEl = {
      _html: '',
      get innerHTML() { return this._html; },
      set innerHTML(v) { this._html = v; },
      querySelector: (sel) => {
        if (sel === '.container') return containerObj;
        return null;
      },
      querySelectorAll: () => []
    };
    try {
      await renderSearch(mockEl);
      const html = mockEl.innerHTML;
      // Extract count from "(X)" in title or result cards
      const countMatch = html.match(/page-title[^>]*>.*?\((\d+)\)/);
      const count = countMatch ? parseInt(countMatch[1], 10) : 0;
      
      const hasError = html.includes('Could not load') || html.includes('NaN');
      let ok = true;
      let reason = '';

      if (hasError) {
        ok = false;
        reason = 'Rendered error or NaN';
      } else if (tc.checkAlt) {
        // Direct routes or alternative routes should appear
        if (count === 0 && !html.includes('Alternative route') && !html.includes('bj-alt-route')) {
          ok = false;
          reason = 'Neither direct nor alternative route found';
        }
      } else if (tc.minResults !== undefined && count < tc.minResults) {
        ok = false;
        reason = `Expected >= ${tc.minResults} results, got ${count}`;
      } else if (tc.maxResults !== undefined && count > tc.maxResults) {
        ok = false;
        reason = `Expected <= ${tc.maxResults} results, got ${count}`;
      }

      if (ok) {
        console.log(`[PASS] ${tc.name} -> ${count} results`);
        passed++;
      } else {
        console.error(`[FAIL] ${tc.name} -> ${reason}`);
        failed++;
      }
    } catch (err) {
      console.error(`[ERROR] ${tc.name} threw exception:`, err);
      failed++;
    }
  }

  // Test Autocomplete
  console.log('\nTesting Autocomplete (acFind)...');
  const acTests = ['Kol', 'Bank', 'Digh', 'Silig', 'Sant'];
  for (const q of acTests) {
    const results = window.acFind ? window.acFind(q) : [];
    if (results && results.length > 0) {
      console.log(`[PASS] acFind("${q}") -> ${results.length} suggestions: ${results.slice(0, 3).join(', ')}...`);
      passed++;
    } else {
      console.error(`[FAIL] acFind("${q}") returned 0 suggestions`);
      failed++;
    }
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed.`);
  if (failed > 0) process.exit(1);
}

runTests().catch(e => {
  console.error('Test runner fatal error:', e);
  process.exit(1);
});
