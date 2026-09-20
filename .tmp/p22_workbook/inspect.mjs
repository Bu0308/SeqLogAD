import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const input = await FileBlob.load("/Users/apple/study/DACNTT/Bang_ke_hoach_SeqLogAD.xlsx");
const workbook = await SpreadsheetFile.importXlsx(input);
const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 8000,
  tableMaxRows: 6,
  tableMaxCols: 12,
  tableMaxCellChars: 120,
});
console.log(summary.ndjson);
const tasks = await workbook.inspect({
  kind: "region",
  sheetId: "Task Register",
  range: "A10:N18",
  maxChars: 10000,
});
console.log(tasks.ndjson);
const style = await workbook.inspect({
  kind: "computedStyle",
  sheetId: "Task Register",
  range: "J13:L16",
  maxChars: 5000,
});
console.log(style.ndjson);
const preview = await workbook.render({
  sheetName: "Task Register",
  range: "A10:N18",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(
  "/Users/apple/study/DACNTT/.tmp/p22_workbook/before.png",
  new Uint8Array(await preview.arrayBuffer()),
);
