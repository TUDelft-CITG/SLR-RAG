module.exports = async (params) => {
    const { app, quickAddApi, variables, obsidian } = params;
    const parentFolder = "all_papers";
    console.log(`[DEBUG] Looking for subfolders in: ${parentFolder}`);

    // --- Step 1: Check if parent folder exists ---
    const parentAbstract = app.vault.getAbstractFileByPath(parentFolder);
    if (!parentAbstract) {
        console.error(`[ERROR] Folder "${parentFolder}" does not exist.`);
        new obsidian.Notice(`❌ Error: Folder "${parentFolder}" does not exist.`);
        return;
    }
    if (parentAbstract instanceof obsidian.TFile) {
        console.error(`[ERROR] "${parentFolder}" is a file, not a folder.`);
        new obsidian.Notice(`❌ Error: "${parentFolder}" is a file, not a folder.`);
        return;
    }

    // --- Step 2: Get all files and folders in the vault ---
    const allAbstractFiles = app.vault.getAllLoadedFiles();
    console.log(`[DEBUG] Total abstract files in vault: ${allAbstractFiles.length}`);

    // --- Step 3: Filter for immediate subfolders of parentFolder ---
    const subfolders = [];
    for (const abstractFile of allAbstractFiles) {
        // Skip if it's a file
        if (abstractFile instanceof obsidian.TFile) continue;

        // Check if it's a direct child of parentFolder
        const pathParts = abstractFile.path.split("/");
        if (pathParts.length === 2 && pathParts[0] === parentFolder) {
            subfolders.push(abstractFile);
            console.log(`[DEBUG] Found subfolder: ${abstractFile.path}`);
        }
    }

    // --- Step 4: Show selection window if subfolders exist ---
    if (subfolders.length === 0) {
        console.warn(`[WARNING] No subfolders found in "${parentFolder}".`);
        new obsidian.Notice(`⚠️ No subfolders found in "${parentFolder}".`);
        return;
    }

    console.log(`[DEBUG] Found ${subfolders.length} subfolders in "${parentFolder}"`);

    // Create a list of subfolder names for the user to choose from
    const subfolderNames = subfolders.map(folder => folder.path.replace(`${parentFolder}/`, ""));
    const subfolderPaths = subfolders.map(folder => folder.path);

    // Use Obsidian's built-in suggester to let the user select a subfolder
    const selectedSubfolderName = await quickAddApi.suggester(
        subfolderNames,
        subfolderNames,
        `Select a subfolder in "${parentFolder}" to open all its markdown files`
    );

    if (!selectedSubfolderName) {
        console.log(`[DEBUG] User cancelled selection.`);
        return;
    }

    // Get the full path of the selected subfolder
    const selectedSubfolderPath = `${parentFolder}/${selectedSubfolderName}`;
    console.log(`[DEBUG] User selected: ${selectedSubfolderPath}`);

    // --- Step 5: Get all markdown files in the selected subfolder ---
    const allMarkdownFiles = app.vault.getMarkdownFiles();
    const filesToOpen = allMarkdownFiles.filter(file => {
        // Include files directly in the subfolder or in its subfolders
        return file.path.startsWith(`${selectedSubfolderPath}/`) ||
               file.path === `${selectedSubfolderPath}.md`;
    });

    console.log(`[DEBUG] Found ${filesToOpen.length} markdown files in "${selectedSubfolderPath}"`);

    if (filesToOpen.length === 0) {
        new obsidian.Notice(`⚠️ No markdown files found in "${selectedSubfolderPath}".`);
        console.warn(`[WARNING] No markdown files found in "${selectedSubfolderPath}".`);
        return;
    }

    // --- Step 6: Open all markdown files in new tabs ---
    console.log(`[DEBUG] Opening ${filesToOpen.length} files...`);
    new obsidian.Notice(`📖 Opening ${filesToOpen.length} files from "${selectedSubfolderPath}"...`);

    for (const file of filesToOpen) {
        await app.workspace.getLeaf(true).openFile(file);
        console.log(`[DEBUG] Opened: ${file.path}`);
    }

    console.log(`✅ SUCCESS: Opened all markdown files in "${selectedSubfolderPath}".`);
    new obsidian.Notice(`✅ Opened ${filesToOpen.length} files from "${selectedSubfolderName}"`);
};