The server is responsible for doing all the processing based on configuration stored in the database.

WebPages

- / - Landing page
- /partners - Table with all partners. Load all at the same time now
- /partners/[partner_id] - Show single partner. No need to have special API because we can pull partner out of the /partners response
- /partners/[partner_id]/files - Show table with files for this partner. Basically the same view as /files/
- /files/ - Table with all processed files. Most recent first. Filters by partner
- /files/[file_id] - Show the file info and table of records
- /files/[file_id]/process_errors - Show file info table of records, but only errors, and allow editing
