const critical = require('critical');
const fs = require('fs');
const path = require('path');

const htmlDir = path.join(__dirname, 'evolves', 'www.evolves.tech'); // change to your static folder
const pages = fs.readdirSync(htmlDir).filter(file => file.endsWith('.html'));

async function processPages() {
  for (const file of pages) {
    const filePath = path.join(htmlDir, file);
    console.log(`Processing ${file}...`);
    try {
      await critical.generate({
        base: htmlDir,
        src: file,
        target: file,
        inline: true,
        minify: true,
        extract: false,
        dimensions: [
          {
            width: 375,
            height: 812, // typical mobile
          },
          {
            width: 1280,
            height: 800, // typical desktop
          },
        ],
      });
      console.log(`Done: ${file}`);
    } catch (error) {
      console.error(`Failed to process ${file}:`, error);
    }
  }
}

processPages();
