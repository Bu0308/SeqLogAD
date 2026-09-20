import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourcePath = "/Users/apple/study/DACNTT/Bang_ke_hoach_SeqLogAD.xlsx";
const outputPath = "/Users/apple/study/DACNTT/outputs/p22-workbook/Bang_ke_hoach_SeqLogAD.xlsx";
const previewPath = "/Users/apple/study/DACNTT/.tmp/p22_workbook/after.png";

await fs.mkdir("/Users/apple/study/DACNTT/outputs/p22-workbook", { recursive: true });
const input = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(input);
const tasks = workbook.worksheets.getItem("Task Register");

tasks.getRange("K15").values = [["In progress"]];
await workbook.recalculate();

const changed = await workbook.inspect({
  kind: "table",
  range: "Task Register!A13:K16",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 12,
  maxChars: 12000,
});
console.log(changed.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "Task Register",
  range: "A10:K18",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, previewPath }));
