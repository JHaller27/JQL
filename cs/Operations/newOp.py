import sys

CLS_NAME=f"{sys.argv[1]}Expression"
PATH=f"./{CLS_NAME}.cs"

print(f"Creating {PATH} from template...")
with open(PATH, "w") as fout:
    template = f'''using System;

namespace Operations {{
    class {CLS_NAME} : Expression {{
        public override int RequiredArgs()
        {{
            throw new NotImplementedException();
        }}

        public override Operation Clone(Operation[] args)
        {{
            throw new NotImplementedException();
        }}

        public override bool CanParse(string token)
        {{
            throw new NotImplementedException();
        }}

        protected override string EvaluateAsString()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as a string");
        }}

        protected override int EvaluateAsInt()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as an integer");
        }}

        protected override double EvaluateAsDouble()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as a double");
        }}

        protected override bool EvaluateAsBool()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as a boolean");
        }}
    }}
}}
'''
    fout.write(template)
