# R script to create an UpSet plot from a CSV with True/False columns

# Install required packages if not already installed
if (!require("UpSetR")) install.packages("UpSetR")
if (!require("ggplot2")) install.packages("ggplot2")
if (!require("dplyr")) install.packages("dplyr")

library(UpSetR)
library(ggplot2)
library(dplyr)

# Read CSV file (replace the path with your file)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("Please provide the CSV file path as argument: Rscript upset_plot.R your_file.csv")
}

csv_path <- args[1]
data <- read.csv(csv_path, stringsAsFactors = FALSE)

# Convert True/False strings to logical
data_logical <- data %>% 
  mutate(across(everything(), ~ ifelse(.x == "True", TRUE, FALSE)))

# Convert to list of sets format expected by UpSetR
set_list <- lapply(names(data_logical), function(col) {
  which(data_logical[[col]] == TRUE)
})
names(set_list) <- names(data_logical)

# Create UpSet plot
p <- upset(
  fromList(set_list),
  nsets = ncol(data_logical),
  order.by = "freq",
  mainbar.y.label = "Number of elements",
  sets.x.label = "Sets",
  point.size = 3,
  line.size = 1,
  mb.ratio = c(0.7, 0.3)
)

# Extract base filename without extension
base_name <- tools::file_path_sans_ext(csv_path)

# Save as JPEG (using grDevices)
jpeg(paste0(base_name, "_upset.jpg"), width = 1200, height = 800, res = 100)
print(p)
dev.off()

# Print confirmation
cat("UpSet plot saved to:")
cat(paste0(base_name, "_upset.jpg"))
