/**
 * Test navigation links on all pages
 * Run with: node test_navigation.js
 */

const http = require('http');

const BASE_URL = 'http://localhost:8000';

// Expected navigation structure for each page
const expectedNavigation = {
    '/classes': [
        { href: '/classes', text: 'My Classes' },
        { href: '/sessions', text: 'All Meetings' }
    ],
    '/sessions': [
        { href: '/classes', text: 'My Classes' },
        { href: '/sessions', text: 'All Meetings' }
    ],
    '/student?code=DZ5NatBCcBQr3f1A8NbDwr9nXKzhwjke': [
        { href: '/', text: 'Home' }
    ]
};

function fetchPage(path) {
    return new Promise((resolve, reject) => {
        http.get(`${BASE_URL}${path}`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        }).on('error', reject);
    });
}

function extractNavLinks(html) {
    const links = [];
    // Extract nav-link anchors
    const linkRegex = /<a[^>]+href="([^"]+)"[^>]+class="nav-link"[^>]*>([^<]+)</g;
    let match;
    while ((match = linkRegex.exec(html)) !== null) {
        links.push({ href: match[1], text: match[2].replace(/[^\w\s]/g, '').trim() });
    }
    return links;
}

async function testNavigation() {
    console.log('🧪 Testing Navigation Links\n');
    let passed = 0;
    let failed = 0;

    for (const [page, expected] of Object.entries(expectedNavigation)) {
        console.log(`Testing ${page}...`);
        try {
            const html = await fetchPage(page);
            const actualLinks = extractNavLinks(html);

            // Check if page has navigation
            if (actualLinks.length === 0 && expected.length > 0) {
                console.log(`  ❌ FAIL: No navigation found`);
                failed++;
                continue;
            }

            // Check each expected link
            let pagePass = true;
            for (const exp of expected) {
                const found = actualLinks.some(link =>
                    link.href === exp.href && link.text.includes(exp.text.replace(/[^\w\s]/g, '').trim())
                );
                if (!found) {
                    console.log(`  ❌ FAIL: Missing link "${exp.text}" (${exp.href})`);
                    console.log(`  Found: ${JSON.stringify(actualLinks)}`);
                    pagePass = false;
                    failed++;
                }
            }

            if (pagePass) {
                console.log(`  ✅ PASS: All links correct`);
                passed++;
            }

        } catch (error) {
            console.log(`  ❌ ERROR: ${error.message}`);
            failed++;
        }
        console.log('');
    }

    console.log(`\n📊 Results: ${passed} passed, ${failed} failed\n`);
    process.exit(failed > 0 ? 1 : 0);
}

testNavigation();
