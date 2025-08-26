import os
import importlib.util


OUTPUTS = {}


def register_output(output):
    """Decorator to register a output"""
    OUTPUTS[output.__name__] = output
    return output


def get_output(output_name):
    """Function to return a output by name"""
    # Handle "default" outputs
    if output_name == None:
        return default_output

    return OUTPUTS[output_name]


def default_output(value, metadata):
    """Default output method; print the value, followed by a table of its metadata"""
    # Calculate the width of the box we're going to draw
    longest_k = 0
    longest_v = 0
    for k, v in metadata.items():
        longest_k = max(longest_k, len(k))
        longest_v = max(longest_v, len(v))
    overall_width = longest_k + longest_v + 2

    # Draw a pretty box with the data
    print("┏" + "━" * overall_width + "┓")
    value_string = "{0:^%d}" % overall_width
    try:
        print("┃" + value_string.format(value) + "┃")
    except:
        # If the value doesn't format, just print it unformatted
        print(value)
    print("┣" + "━" * overall_width + "┫")
    for k, v in metadata.items():
        metadata_string = "{0:>%d}: {1:<%d}" % (longest_k, longest_v)
        print("┃" + metadata_string.format(k, v) + "┃")
    print("┗" + "━" * overall_width + "┛")


def find_outputs():
    """Import files in current directory to find outputs"""
    for dirpath, dirnames, filenames in os.walk("."):
        for filename in [f for f in filenames if f.endswith(".py")]:
            # Construct the module name from the file path
            module_name = os.path.splitext(filename)[0]
            # Construct the full path to the .py file
            file_path = os.path.join(dirpath, filename)
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)


def output_results(result_df):
    """
    Process a result df row by row;
    for each row find the correct output process and send the results to it
    """
    for i, result_row in result_df.iterrows():
        # Spereate the data, metadata and output function
        output_name = result_row.pop("output")
        result_value = result_row.pop("value")
        result_metadata = result_row.to_dict()
        # Retrieve and utilize output funciton
        output_function = get_output(output_name)
        output_function(result_value, result_metadata)
