import logging
script_dir = os.path.dirname(os.path.abspath(__file__))
# --- Define the file path *relative* to this script ---
data_file_path = os.path.join(script_dir, 'parsed_itch_data.jsonl')

try:
    with open(data_file_path ,'r',encoding='utf-16-le') as f:
        logging.info(f"")

    pass
except:
    pass