using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace Operations
{
    class PathPrimitive : Primitive
    {
        private static Regex OperationRegex = new Regex(@"^(?<part>(\.\w+)|(\[\d*\]))+$");

        private IDictionary<string, dynamic> Json { get; set; }

        private string[] PathElements { get; set; }

        public PathPrimitive(string arg, IDictionary<string, dynamic> json) : base(arg)
        {
            Json = json;
        }

        public override Operation ClonePrimitive(string arg)
        {
            return new PathPrimitive(arg, Json);
        }

        public override bool CanParse(string token)
        {
            return OperationRegex.IsMatch(token);
        }

        private static dynamic Traverse(string[] path, dynamic json)
        {
            dynamic curr = json;

            Queue<string> pathQueue = new Queue<string>(path);

            for(string part; pathQueue.TryDequeue(out part); )
            {
                // Move curr as key
                if (part[0] == '.')
                {
                    string key = part.Substring(1);

                    IDictionary<string, dynamic> currDict;
                    try {
                        currDict = (IDictionary<string, dynamic>) curr;
                    }
                    catch (Exception)
                    {
                        currDict = ((List<KeyValuePair<string, dynamic>>) curr).ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
                    }

                    if ( ! currDict.TryGetValue(key, out curr) )
                    {
                        return null;
                    }
                }

                // Move curr as index
                else if (part[0] == '[' && part[part.Length - 1] == ']')
                {
                    string idxStr = part.Substring(1, part.Length - 2).Trim();

                    // Ambiguous indexing - return array of all elements
                    if (idxStr == "")
                    {
                        IList<dynamic> subParts = new List<dynamic>();

                        foreach (dynamic item in ((dynamic[]) curr))
                        {
                            subParts.Add(Traverse(pathQueue.ToArray(), curr));
                        }

                        return subParts.ToArray();
                    }

                    // Specific index
                    int idx = int.Parse(idxStr);
                    curr = ((dynamic[]) curr)[idx];
                }
                else
                {
                    throw new FormatException($"Invalid property-path format '{part}'");
                }
            }

            return curr;
        }

        private static string[] SplitPath(string path)
        {
            Regex partRegex = new Regex(@"(?<part>(\.\w+)|(\[\d*\]))");

            return partRegex.Matches(path)
                .Select(m => m.Groups["part"].Value)
                .ToArray();
        }

        internal override string EvaluateAsString()
        {
            string[] pathParts = SplitPath(Arg);

            return (string) Traverse(pathParts, Json);
        }

        internal override int EvaluateAsInt()
        {
            string[] pathParts = SplitPath(Arg);

            return (int) Traverse(pathParts, Json);
        }

        internal override double EvaluateAsDouble()
        {
            string[] pathParts = SplitPath(Arg);

            return (int) Traverse(pathParts, Json);
        }

        internal override bool EvaluateAsBool()
        {
            string[] pathParts = SplitPath(Arg);

            return (bool) Traverse(pathParts, Json);
        }

        internal override dynamic[] EvaluateAsArray()
        {
            string[] pathParts = SplitPath(Arg);

            return (dynamic[]) Traverse(pathParts, Json);
        }

        internal override IDictionary<string, dynamic> EvaluateAsObject()
        {
            string[] pathParts = SplitPath(Arg);

            return (IDictionary<string, dynamic>) Traverse(pathParts, Json);
        }
    }
}
