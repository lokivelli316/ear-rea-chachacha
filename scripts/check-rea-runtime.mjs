const [major, minor, patch] = process.versions.node.split('.').map(Number);
const atLeast = (m, n, p) =>
  major > m || (major === m && (minor > n || (minor === n && patch >= p)));

const ok =
  (major === 22 && atLeast(22, 23, 4)) ||
  (major === 24 && atLeast(24, 22, 1)) ||
  atLeast(26, 12, 1);

const receipt = {
  capability: 'reverse-engineering.rea',
  package: 'rea-agents@6.8.0',
  node: process.versions.node,
  required: '^22.23.4 || ^24.22.1 || >=26.12.1',
  status: ok ? 'PASS' : 'ENVIRONMENT BLOCKED'
};

console.log(JSON.stringify(receipt, null, 2));
process.exit(ok ? 0 : 2);
