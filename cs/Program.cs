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
            IDictionary<string, dynamic> json;

            try
            {
                string filePath = Path.Combine(root, fileName);
                json = GetJson(filePath);
            }
            catch (JsonReaderException)
            {
                Console.Error.WriteLine($"File at '{fileName}' is not valid JSON");
                return false;
            }

            Operation[] prototypePool = new Operation[]
            {
                // Must be in Order of Operations
                new NotExpression(null),
                new AndExpression(null),
                new OrExpression(null),
                new EqualsExpression(null),
                new NotEqualsExpression(null),
            };

            Operation operationTree;
            try
            {
                operationTree = Parse(prototypePool, expressionTokens);
            }
            catch (InvalidOperationException)
            {
                Console.Error.WriteLine("Invalid expression");
                return false;
            }

            bool retv = operationTree.Evaluate();

            return retv;
        }

        static IDictionary<string, dynamic> GetJson(string filePath)
        {
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