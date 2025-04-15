import re
import win32clipboard

def combinemd(filepaths):
    """
    Combines the text content of multiple Markdown files into a single string.

    Args:
        filepaths: A list of paths to Markdown files.

    Returns:
        A string containing the combined text of all files, with the content
        of each subsequent file appended to the content of the previous file,
        separated by two newlines.  Returns an empty string if the input list
        is empty or if no files could be read. Returns the content of a single
        file if only one filepath is provided.
    """
    combined_content = ""
    if not filepaths:  # Handle empty list case
        return ""

    for filepath in filepaths:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if combined_content:  # Add newlines only if there's existing content
                    combined_content += "\n\n"
                combined_content += content
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            # Continue to the next file
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            # Continue to the next file
    return combined_content
    
def md_to_string_with_addition(filepath, additional_line):
    """Reads a Markdown file, appends a line, and returns the combined string.

    Args:
        filepath: The path to the Markdown file.
        additional_line: The string to append to the Markdown content.

    Returns:
        The combined string (Markdown content + newline + additional_line),
        or None if an error occurs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            md_content = file.read()

        return f"{md_content}\n\n{additional_line}"  # Add two newlines for better separation

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def copy_md_file(source_filepath, destination_filepath):
    """Copies the entire content of one markdown file to another.

    Args:
        source_filepath: The path to the source markdown file.
        destination_filepath: The path to the destination markdown file.
           If the destination file exists, it will be overwritten.
           If the destination file does not exist, it will be created.
    """
    try:
        # Open the source file in read mode ("r")
        with open(source_filepath, "r", encoding="utf-8") as source_file:  # Specify UTF-8 encoding for proper handling of special characters
            # Read the entire content of the source file
            content = source_file.read()

        # Open the destination file in write mode ("w")
        with open(destination_filepath, "w", encoding="utf-8") as destination_file:  # Use UTF-8 encoding here too.
            # Write the content to the destination file
            destination_file.write(content)

        print(f"Successfully copied content from '{source_filepath}' to '{destination_filepath}'")

    except FileNotFoundError:
        print(f"Error: Source file '{source_filepath}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def modfilewrite(text, filename):
    """Writes a modified string to a text file.

    Args:
        text: The string to modify and write.
        filename: The name of the file to create or overwrite.
    """
    try:
        # Normalize line endings to \n BEFORE any processing
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove first and last characters (correct slicing)
        if len(text) > 8:
            modified_text = text
        else:
            modified_text = ""

        # Replace "&&&" with "```"
        modified_text = modified_text.replace("&&&", "```")

        # Function to remove backticks AND asterisks from markdown comments
        def remove_chars_from_comment(match):
            comment_content = match.group(1)
            # Remove backticks and asterisks
            comment_content = comment_content.replace('`', '').replace('*', '')

            # Remove words with more than one single or double quote
            words = comment_content.split()
            filtered_words = []
            for word in words:
                single_quote_count = word.count("'")
                double_quote_count = word.count('"')
                if single_quote_count <= 1 and double_quote_count <= 1:
                    filtered_words.append(word)
            comment_content = ' '.join(filtered_words)


            return f"<!--{comment_content}-->"


        # Use regex to find all markdown comments and process them
        modified_text = re.sub(r"<!--(.*?)-->", remove_chars_from_comment, modified_text, flags=re.DOTALL)

        final_text = modified_text

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"Modified string successfully written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")