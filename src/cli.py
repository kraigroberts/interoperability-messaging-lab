import argparse

def main():
    parser = argparse.ArgumentParser(description="Interoperability Messaging Lab CLI")
    parser.add_argument('--in', dest='input_file', required=False, help='Input file path')
    parser.add_argument('--out', dest='output_file', required=False, help='Output file path')
    args = parser.parse_args()

    print("CLI started. Input:", args.input_file, "Output:", args.output_file)

if __name__ == "__main__":
    main()
