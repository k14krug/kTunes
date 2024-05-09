import numpy as np

# Define the percentages for each category
percentages = [10, 15, 20, 5, 25, 25]

# Specify the total number of items to distribute
total_items = 250

# Specify the categories
categories = ["RecentAdd", "Latest", "In Rot", "Other", "Old", "Album"]

# Calculate the number of items for each category based on percentages
category_counts = [int((percentage / 100) * total_items) for percentage in percentages]

# Calculate initial fractions for each category
fractions = [1 / count for count in category_counts]

# Initialize an empty list to store the resulting distribution
result_distribution = []

# Create a loop to distribute items evenly
while len(result_distribution) < total_items:
    # Find the index of the category with the lowest fraction
    min_fraction_index = np.argmin(fractions)
    
    # Calculate the current count for the selected category
    current_count = len([entry for entry in result_distribution if categories[min_fraction_index] in entry])
    
    # Calculate the total count for the selected category
    category_count = category_counts[min_fraction_index]
    
    # Update the fraction for the selected category
    fractions[min_fraction_index] += 1 / category_count
    
    # Add the entry to the result list
    result_distribution.append(f"{categories[min_fraction_index]}, {current_count + 1} of {category_count}")

# Print the final distribution
for entry in result_distribution:
    print(entry)
