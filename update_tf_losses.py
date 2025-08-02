import os
import glob

def find_and_replace_in_files(directory, old_string, new_string):
    """
    Finds and replaces a string in all .py files in a given directory and its subdirectories,
    excluding the .venv folder.
    """
    count = 0
    for filepath in glob.iglob(os.path.join(directory, '**', '*.py'), recursive=True):
        if '.venv' in filepath:
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if old_string in content:
                print(f"Found '{old_string}' in: {filepath}")
                new_content = content.replace(old_string, new_string)
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print(f"Replaced with '{new_string}' in: {filepath}")
                count += 1
        except Exception as e:
            print(f"Error processing file {filepath}: {e}")
            
    return count

if __name__ == "__main__":
    project_directory = '.' 
    old_tf_loss_function = 'tf.compat.v1.losses.sparse_softmax_cross_entropy'
    new_tf_loss_function = 'tf.compat.v1.losses.sparse_softmax_cross_entropy'
    
    print(f"Searching for '{old_tf_loss_function}' and replacing with '{new_tf_loss_function}'...")
    
    replaced_count = find_and_replace_in_files(project_directory, old_tf_loss_function, new_tf_loss_function)
    
    if replaced_count > 0:
        print(f"\nSuccessfully replaced {replaced_count} occurrences.")
    else:
        print("\nNo occurrences found to replace.")
