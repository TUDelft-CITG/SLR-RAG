module.exports = async (params) => {
    const { app } = params;
    const { update, getPropertiesInFile } = app.plugins.plugins["metaedit"].api;

    const file = app.workspace.getActiveFile();
    if (!file) return new Notice("🗑️ No file open");

    // Update tags property
    await update("tags", "#remove", file.path);
    new Notice("🗑️ #remove");
};