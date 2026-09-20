/* Render harness: actually evaluates js/bus-page.js and renders a mock bus.
   Catches broken concatenation that node --check cannot (ASI hazard).
   Usage: node scripts/render_test.js  (from repo root) */
const fs = require('fs');

global.window = { prompt: () => null, alert: () => {} };
global.location = { hash: '#/bus/testbus', href: 'https://busjatri.in/#/bus/testbus' };
global.history = { length: 2 };
global.localStorage = { getItem: () => null, setItem: () => {} };
global.BUSES = {
  testbus: {
    bus_name: 'TEST BUS', reg_no: 'WB29B1394', origin: 'Bankura', destination: 'Asansol',
    departure_time: '7:30 AM', arrival_time: '11:45 AM', operator: 'Test Travels',
    stoppage_pages: [
      { name: 'Bankura', up_time: '7:30 AM', down_time: '5:20 PM' },
      { name: 'Chhatna', up_time: '8:05 AM', down_time: '4:40 PM' },
      { name: 'Asansol', up_time: '11:45 AM', down_time: '1:10 PM' }
    ]
  }
};
global.STOPS = {};
global.DATA = { meta: { last_updated: '2026-09-20' } };
global.esc = (x) => String(x == null ? '' : x).replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>').replace(/"/g, '"');
global.pn = (x) => String(x == null ? '' : x);
global.busTypeBadge = () => '<span>PRIVATE</span>';
global.icon = (n) => '<i class="ic ic-' + n + '"></i>';
global.loadWeather = () => {};

let captured = '';
const el = { set innerHTML(v) { captured = v; }, get innerHTML() { return captured; } };

eval(fs.readFileSync('js/bus-page.js', 'utf8'));

(async () => {
  await renderBus(el, 'testbus');
  const fail = [];
  const must = [
    ['wa-row', 'action row'],
    ['class="map-btn"', 'map button'],
    ['class="wa-btn"', 'whatsapp button'],
    ['class="fb-btn"', 'facebook button'],
    ['class="report-btn"', 'report button'],
    ['toggleReport(this)', 'report wiring'],
    ['shareBusWhatsApp()', 'whatsapp wiring'],
    ['shareBusFacebook()', 'facebook wiring'],
    ['Route Timetable', 'timetable heading'],
    ['schedule-table', 'timetable table'],
    ['stop-list', 'stoppage list'],
    ['Chhatna', 'stop row content'],
    ['Data updated', 'footer line']
  ];
  for (const [needle, what] of must) if (!captured.includes(needle)) fail.push('MISSING: ' + what + ' (' + needle + ')');
  const rowStart = captured.indexOf('wa-row');
  const rowEnd = captured.indexOf('</div>', rowStart);
  const row = captured.slice(rowStart, rowEnd);
  const svgs = (row.match(/<svg/g) || []).length;
  if (svgs < 4) fail.push('MISSING: svg icons in action row (found ' + svgs + ')');
  if (svgs > 4) fail.push('TOO MANY svgs in action row (found ' + svgs + ')');
  if (fail.length) { console.error(fail.join('\n')); process.exit(1); }
  console.log('RENDER OK: action row + timetable render correctly (' + captured.length + ' chars, 4 icon buttons)');
})().catch((e) => { console.error('RENDER FAILED:', e); process.exit(1); });
