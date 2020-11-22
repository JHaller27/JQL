using System;
using System.IO;
using System.Collections.Generic;
using Newtonsoft.Json;
using System.Threading.Tasks;

using Operations;

namespace JQL
{
    class Program
    {
        static void Main(string[] args)
        {
            Queue<string> argQueue = new Queue<string>(args);

            string dataRoot = argQueue.Dequeue();
            IDictionary<string, dynamic> json = GetJson(dataRoot, "jon_snow.json");

            OperationParser parser = OperationParser.GetInstance(json);
            Operation operationTree = parser.Parse(argQueue);

            bool retv = operationTree.Evaluate();

            Console.WriteLine(retv);
        }

        static IDictionary<string, dynamic> GetJson(string root, string fileName)
        {
            string filePath = Path.Combine(root, fileName);
            string rawJson = File.ReadAllText(filePath);
            IDictionary<string, dynamic> json = JsonConvert.DeserializeObject<Dictionary<string, dynamic>>(rawJson);

            return json;
        }
    }
}