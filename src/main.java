// Brian Fang
// 05/13/2024

import java.io.*;
import java.util.*;
import java.util.concurrent.TimeUnit;

// Test Object - includes test name and each test case
class Test {
    private String testName;
    private ArrayList<String> params;
    public Test(String testName) {
        this.testName = testName;
        this.params = new ArrayList<>();
    }
    public String getTestName() {
        return testName;
    }
    public void addParam(String param) {
        params.add(param);
    }
    public ArrayList<String> getParams() {
        return params;
    }
}

public class main {
	
	public static int count1 = 0;
	public static int count2 = 0;
	public static LinkedHashMap<String, Set<String>> cases = new LinkedHashMap<>();

    public static void main(String[] args) {
    	
    	// ArrayList of tests
        ArrayList<Test> tests = new ArrayList<>();
        
        // Reading log file
        try {
            BufferedReader br = new BufferedReader(new FileReader("src/input.txt"));
            String line = "";
            Test currentTest = null;
            
            // Find test name and corresponding test cases from log
            while ((line = br.readLine()) != null) {
            	
            	// Test name found
                if (line.startsWith("Description")) {
                    String[] words = line.split("\\s+");
                    String testName = words[2];
                    currentTest = new Test(testName);
                    tests.add(currentTest);
                } 
                
                // Corresponding test cases found
                else if (line.startsWith("main_exec_args")) {
                    String param = line.replaceAll("\\s+", "").substring(line.indexOf("="));
                    currentTest.addParam(param);
                    while ((line = br.readLine()) != null && !line.startsWith("search_expr_true")) {
                        currentTest.addParam(line.replaceAll("\\s+", ""));
                    }
                }
            }
            br.close();
            PrintWriter writer = new PrintWriter("src/output.txt");
            
            // Loop through tests
            for (Test test : tests) {
            	// System.out.println("TEST TEST TEST" + test.getTestName());
            	writer.println("=================================================");
                writer.println("TEST LAYER: " + test.getTestName());
                
                // LinkedHashMap to store each unique parameter and its range of values for test
                LinkedHashMap<String, Set<String>> resultMap = new LinkedHashMap<>();
                
                // Loop through test cases
                for (String param : test.getParams()) {
                    StringBuilder paramName = new StringBuilder();
                    paramName.append('-');
                    StringBuilder paramVal = new StringBuilder();
                    boolean addToName = true;
                	
                    // Loop through parameters
                    for (int i = 1; i < param.length(); i++) {
                		
                    	// If next parameter is found, store previous parameter name and value into resultMap
                		if (param.charAt(i) == '-' && Character.isAlphabetic(param.charAt(i + 1))) {
                			
                			// If parameter is already in resultMap, add value onto existing value array
                			if (resultMap.containsKey(paramName + "")) {
                	            resultMap.get(paramName + "").add(paramVal + "");
                	        } 
                			
                			// If new parameter, create new key and value
                			else {
                	            Set<String> values = new HashSet<>();
                	            values.add(paramVal + "");
                	            resultMap.put(paramName + "", values);
                	        }
                			paramName = new StringBuilder();
                			paramVal = new StringBuilder();
                			addToName = true;
                			
                		}
                		
                		// CASE 1: parameter and value are separated by a '=' (ex. -m=5, -yN_rx=1, -gchannel=N)
                		else if (param.charAt(i) == '=') {
                			addToName = false;
                			i++;
                		}
                		
                		// CASE 2: parameter is followed by a number value (ex. -n100, -S-0.6, -e_snr_step.1)
                		else if (Character.isDigit(param.charAt(i)) || param.charAt(i) == '-' || param.charAt(i) == '.') {
                			addToName = false;
                		}
                		
                		// Continue adding to parameter name
                		if (addToName) {
                			paramName.append(param.charAt(i));
                		}
                		
                		// Continue adding to parameter value
                		else {
                			paramVal.append(param.charAt(i));
                		}
                	}
                }
				LinkedHashMap<Integer, ArrayList<String>> methodCode = new LinkedHashMap<>();

                // Creating HashMap of lines and associated methods
				try {
					BufferedReader br2 = new BufferedReader(new FileReader("src/" + test.getTestName() + ".txt"));
					String line2;
					int num = 1;
					String prev = "";
					// Check to see if start of function
					while ((line2 = br2.readLine()) != null) {
						// THIS DOESNT CHECK FOR /* AND */
						if (!line2.contains("}") && line2.contains("{") && !line2.contains("main") && !line2.matches(".*\\/\\*[^*]*\\{[^*]*\\*\\/.*")) {
							if (!line2.matches(".*(['\"]).*\\{.*\\1.*") && !line2.matches(".*//.*\\{.*")) {
								count1++;
								if (line2.trim().charAt(0) == '{') {
									//System.out.println(num + "" + line2);
									// Run recursive method, add result to HashMap
									LinkedHashMap<Integer, ArrayList<String>> temp = recursiveMethod(br2, line2, num, true, prev);
									methodCode.putAll(temp);
									num += temp.size() - 2;
								}
								else {
									// Run recursive method, add result to HashMap
									try {
										LinkedHashMap<Integer, ArrayList<String>> temp = recursiveMethod(br2, line2, num, false, prev);
										methodCode.putAll(temp);
										num += temp.size() - 1;
									}
									catch(Exception e) {
										System.out.println(line2);
									}
									
								}
							}
						}
						num++;
						prev = line2.trim();
					}
					br2.close();
					System.out.println(test.getTestName() + ": " + count1 + ", " + count2 + ", " + (count1 == count2));
					// Printing HashMap for debug
					for (Map.Entry<Integer, ArrayList<String>> entry1 : methodCode.entrySet()) {
						 //System.out.println(entry1.getKey() + ": " + entry1.getValue());
					}
				} 
				catch (IOException e) {
					e.printStackTrace();
				}
                
            	try {
            		BufferedReader tempBr = new BufferedReader(new FileReader("src/" + test.getTestName() + ".txt"));
                	boolean comment = false;
                	boolean skip = false;
                	boolean isCase = false;
                	String caseName = "";
                	String newLine = "";
                	String temp = "";
                	Set<String> vars = new HashSet<>();
        			while ((temp = tempBr.readLine()) != null) {
        				temp = temp.replaceAll("\\s+", "");
        				newLine = temp;
        				if (!comment && ((temp.contains("//") && temp.contains("/*") && temp.indexOf("//") < temp.indexOf("/*")) || (temp.contains("//") && !temp.contains("/*")))) {
        					newLine = temp.substring(0, temp.indexOf("//"));
        				}
        				else if ((temp.contains("/*") && !comment) || (temp.contains("*/") && comment)) {
        					newLine = "";
        					for (int i = 0; i < temp.length(); i++) {

        						if (!comment && i < (temp.length() - 1) && temp.substring(i, i + 2).equals("//")) {
        							break;
        						}
        						else if (!comment && i < (temp.length() - 1) && temp.substring(i, i + 2).equals("/*")) {
        							comment = true;
        							i++;
        						}
        						else if (comment && i < (temp.length() - 1) && temp.substring(i, i + 2).equals("*/")) {
        							comment = false;
        							skip = true;
        							i++;
        						}
        						else if (!comment && !skip) {
        							newLine += temp.charAt(i);
        						}
        						skip = false;
        					}
        				}
        				if (!isCase && newLine.contains("case'")) {
        					isCase = true;
        					caseName = newLine.substring(newLine.indexOf("case'") + 5, newLine.indexOf("':")) + "";
        				}
        				else if (isCase) {
        					if (newLine.contains("break;") || newLine.contains("exit")) {
        						isCase = false;
        						cases.put(caseName, vars);
        						//for (String element : vars) {
                                //    System.out.println(element);
                                //}
        						vars = new HashSet<>();
                            	//System.out.println(caseName);
                            	
        					}
        					if (newLine.matches("[^=]*=[^=]*;")) {
        						if (!newLine.contains("+=") && !newLine.contains("-=")) {
        							if (newLine.split("=")[0].length() > 1) {
                    					vars.add(newLine.split("=")[0]);
        							}
        						}
            				}
        				}
        				
        			}
        			
        		} 
            	catch (IOException e) {
        			e.printStackTrace();
        		}
				
                // Loop through resultMap
                for (Map.Entry<String, Set<String>> entry : resultMap.entrySet()) {
                    String paramName = entry.getKey();
                    Set<String> paramValues = entry.getValue();
                    
                    // Check if value is empty
                    if (paramValues.contains("") && paramName.length() == 3) {
                    	paramValues.add(paramName.charAt(2) + "");
                    	paramName = paramName.substring(0, 2);
                    }
                    // start searching for variables
					paramName = paramName.substring(1, paramName.length());
					writer.println("-------------------------------------------------");
					writer.println("PARAMETER: -" + paramName + ", VARIABLE(S): " + cases.get(paramName));
					writer.println("-------------------------------------------------");
					if (cases.get(paramName) == null) {
						writer.println("NO DATA");
					}
					else {
	                    //writer.print(paramName);
	                    try {
	    					BufferedReader br3 = new BufferedReader(new FileReader("src/" + test.getTestName() + ".txt"));
	    					String line3;
	    					String newLine = "";
	    					boolean comment = false;
	    					boolean skip = false;
	    					int num = 0;
	    			        LinkedHashSet<ArrayList<String>> set = new LinkedHashSet<>();
	    					while ((line3 = br3.readLine()) != null) {
	    						num++;
	    						line3 = line3.trim();
	    						newLine = line3;
	    						if (!comment && ((line3.contains("//") && line3.contains("/*") && line3.indexOf("//") < line3.indexOf("/*")) || (line3.contains("//") && !line3.contains("/*")))) {
	    							line3 = line3.substring(0, line3.indexOf("//"));
	    						}
	    						else if ((line3.contains("/*") && !comment) || (line3.contains("*/") && comment)) {
	    							newLine = "";
	    							for (int i = 0; i < line3.length(); i++) {
	
	    								if (!comment && i < (line3.length() - 1) && line3.substring(i, i + 2).equals("//")) {
	    									break;
	    								}
	    								else if (!comment && i < (line3.length() - 1) && line3.substring(i, i + 2).equals("/*")) {
	    									comment = true;
	    									i++;
	    								}
	    								else if (comment && i < (line3.length() - 1) && line3.substring(i, i + 2).equals("*/")) {
	    									comment = false;
	    									skip = true;
	    									i++;
	    								}
	    								else if (!comment && !skip) {
	    									newLine += line3.charAt(i);
	    								}
	    								skip = false;
	    							}
	    						}
	    						if (containsAnySubstring(newLine, cases.get(paramName))) {
	    							if (methodCode.containsKey(num)) {
	    								set.add(methodCode.get(num));
	    							}
	    							else {
	    								ArrayList<String> temp = new ArrayList<>();
	    								temp.add(newLine);
	    								set.add(temp);
	    							}
	    						}
	    					}
	    					writer.println(set);
	                    }
	                    catch (IOException e) {
	    					e.printStackTrace();
	    				}
					}
                    // writer.println(paramName + " (" + variables + ") -> " + "TEMP" + ": " + String.join(", ", paramValues));
                }
                writer.println();
                count1 = 0;
                count2 = 0;
            }
            writer.close();
            System.out.println("Output written to output.txt");
        }
        catch (IOException e) {
            e.printStackTrace();
        }
    }
    // recur function
    // ALSO CHECK IF { and } are on the same line before doing the try catch while
    // can change func name to hashMethods ?
    public static LinkedHashMap<Integer, ArrayList<String>> recursiveMethod (BufferedReader br, String line, int num, boolean pre, String prev) {
    	ArrayList<Integer> lines = new ArrayList<>();
    	ArrayList<String> code = new ArrayList<>();
    	LinkedHashMap<Integer, ArrayList<String>> methodCode = new LinkedHashMap<>();
    	if (pre == true) {
    		code.add(prev);
    		lines.add(num - 1);
    	}
    	code.add(line.trim());
    	lines.add(num);
    	boolean comment = false;
    	boolean skip = false;
    	try {
			while ((line = br.readLine()) != null) {
				//System.out.println(num + "" + comment);
				num++;
				String original = line.trim();
				line = line.trim(); // <- this is useless
				
				if (!comment && ((line.contains("//") && line.contains("/*") && line.indexOf("//") < line.indexOf("/*")) || (line.contains("//") && !line.contains("/*")))) {
	    			line = line.substring(0, line.indexOf("//"));
	    		}
				// checking if it includes // might be useless bc its else if
				// maybe add in if its not com then check for /*
	    		else if ((line.contains("/*") && !comment) || (line.contains("*/") && comment)) {
	    			// revmoe all comments, update line, if ends in start comment then dont run rest
	    			line = "";
	    			//comment = true; // this turns true whether or not its bc of start com or end com
	    			for (int i = 0; i < original.length(); i++) {
	    				//System.out.println(original.substring(i, i+1));
	    				// when using < lengh - 2, it loops an extra useless time
	    				
	    				// IF NO COM AND FIND COMMENT SUBSTRING
	    				if (!comment && i < (original.length() - 1) && original.substring(i, i + 2).equals("//")) {
	    					break;
	    				}
	    				
	    				// IF NO COM AND FIND START COMMENT, START COMMENT
	    				else if (!comment && i < (original.length() - 1) && original.substring(i, i + 2).equals("/*")) {
	    					comment = true;
	    					i++;
	    					// start looking for end com
	    				}
	    				else if (comment && i < (original.length() - 1) && original.substring(i, i + 2).equals("*/")) {
	    					comment = false;
	    					skip = true;
	    					i++;
	    				}
	    				else if (!comment && !skip) {
	    					line += original.charAt(i);
	    				}
	    				skip = false;
	    			}
	    		}

				// here i can remove quotes too, i can also do it in the above loop, while comment is false look for quote as well
				
				// EVEN MORE ACCURATE: MAKE { } LOGIC SAME AS COMMENT. IF ON LINE SCAN REST OF LINE 
				
				// can do if { } else if { else if } else, in this can check if # of { = # of }, if not then yeah
				// can do if no comment in front, and { is first character, then also add previous line to num and code
				// THE !LINE.CONTAINS("}") IS TEMP FOR WHEN { AND } ARE IN SAME LINE
				if (!line.contains("}") && line.contains("{") && !line.matches(".*\\/\\*[^*]*\\{[^*]*\\*\\/.*")) {
					if (!line.matches(".*(['\"]).*\\{.*\\1.*") && !line.matches(".*//.*\\{.*")) {
						count1++;
						//System.out.println((count1 - count2) + "  " + num + "" + line + " COUNT1:" + count1 + ", COUNT2:" + count2);
						// this doesnt check if theres /* or */ before the { even though it works but its not first
						// i think it works now
						if (line.trim().charAt(0) == '{') {
							code.remove(code.size() - 1);
							lines.remove(lines.size() - 1);
							// remove most recent from code and lines. then add prev num + prev line to new
							LinkedHashMap<Integer, ArrayList<String>> temp = recursiveMethod(br, line, num, true, prev);
							methodCode.putAll(temp);
							code.addAll(temp.get(num));
							num += temp.size() - 2;
						}
						else {
							LinkedHashMap<Integer, ArrayList<String>> temp = recursiveMethod(br, line, num, false, prev);
							methodCode.putAll(temp);
							code.addAll(temp.get(num + 1));
							num += temp.size() - 1;
						}
						
					}
				}
				else if (!line.contains("{") && line.contains("}") && !line.matches(".*\\/\\*[^*]*\\}[^*]*\\*\\/.*")) {
					if (!line.matches(".*(['\"]).*\\}.*\\1.*") && !line.matches(".*//.*\\}.*")) {
						if (line.contains("{")) {
							String temp = line;
							String temp2 = line;
							//System.out.print(temp2.replaceAll("\\{", "00").length() - line.length());
							//System.out.println(temp.replaceAll("\\}", "00").length() - line.length());
						}
						count2++;
						//System.out.println((count1 - count2) + "  " + num + "" + line + " COUNT1:" + count1 + ", COUNT2:" + count2);
						code.add(original);
						lines.add(num);
						break;
					}
				
				}
				else {
					code.add(original);
					lines.add(num);
				}
				prev = original;
			}
		} 
    	catch (IOException e) {
			e.printStackTrace();
		}
    	
    	// Add code to each line
    	for (int i = 0; i < lines.size(); i++) {
    		methodCode.put(lines.get(i), code);
    	}
    	return methodCode;
    }
    public static boolean containsAnySubstring(String str, Set<String> set) {
        for (String s : set) {
            if (str.contains(s)) {
                return true;
            }
        }
        return false;
    }
}