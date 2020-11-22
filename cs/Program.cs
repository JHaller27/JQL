using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Newtonsoft.Json;

using Operations;

namespace JQL
{
    class Program
    {
        static void Main(string[] args)
        {
            Queue<string> argQueue = new Queue<string>(args);

            string dataRoot = argQueue.Dequeue();
            Queue<string> expressionTokens = new Queue<string>(argQueue);

            bool retv = FilePasses(dataRoot, "jon_snow.json", expressionTokens);

            Console.WriteLine(retv);
        }

        static bool FilePasses(string root, string fileName, Queue<string> expressionTokens)
        {
            IDictionary<string, dynamic> json = GetJson(root, fileName);

            Operation[] prototypePool = new Operation[]
            {
                // Must be in Order of Operations
            };

            Operation operationTree = Parse(prototypePool, expressionTokens);

            bool retv = operationTree.Evaluate();

            return retv;
        }

        static IDictionary<string, dynamic> GetJson(string root, string fileName)
        {
            string filePath = Path.Combine(root, fileName);
            string rawJson = File.ReadAllText(filePath);
            IDictionary<string, dynamic> json = JsonConvert.DeserializeObject<Dictionary<string, dynamic>>(rawJson);

            return json;
        }

        static Operation Parse(Operation[] prototypePool, Queue<string> tokens)
        {
            string token;
            while (tokens.TryDequeue(out token))
            {
                Operation prototype = prototypePool.First(prototype => prototype.CanParse(token));

                if (prototype.IsPrimitive())
                {
                    return prototype.ClonePrimitive(token);
                }

                int numArgs = prototype.RequiredArgs();
                Operation[] args = new Operation[numArgs];
                for (int i = 0; i < numArgs; i++)
                {
                    args[i] = Parse(prototypePool, tokens);
                }

                return prototype.Clone(args);
            }

            throw new ArgumentException("Token Queue passed to Parse was empty - no tokens to parse.");
        }
    }
}