from typing import NamedTuple
from enum import Enum


class UserInputType(Enum):
    COMMAND = 1
    ARGUMENT = 2
    STRING_LITERAL = 3

class ParsedUserInput(NamedTuple):
    parsed_values: list[tuple[UserInputType, str]]
    command: str
    args: list[str]

def process_user_input(raw_user_input: str) -> ParsedUserInput:
    
    user_input = raw_user_input.strip()
    
    parsing_user_command = False
    user_command_complete = False
    parsing_string_literal = False
    parsing_word = True
    
    parsed_values: list[tuple[UserInputType, str]] = [(UserInputType.COMMAND, "")]
    parsed_values_index = 0
    
    user_command: str = ""
    
    user_args: list[str] = [""]
    current_user_args_index = 0
    
    user_literal_strings: list[str] = [""]
    current_user_literal_strings_index = 0
    
    for char in user_input:
        if user_command_complete:
            if parsing_string_literal:
                if char == "'":
                    parsing_string_literal = False
                    current_user_literal_strings_index += 1
                    user_literal_strings.append("")
                    parsed_values_index += 1
                    parsed_values.append((UserInputType.STRING_LITERAL, ""))
                else:
                    user_literal_strings[current_user_literal_strings_index] += char
                    parsed_values[parsed_values_index] = (UserInputType.STRING_LITERAL, user_literal_strings[current_user_literal_strings_index])
            else:
                if char == "'":
                    parsing_string_literal = True
                else:
                    if char == " ":
                        if parsing_word:
                            parsing_word = False
                            current_user_args_index += 1
                            user_args.append("")
                            parsed_values_index += 1
                            parsed_values.append((UserInputType.ARGUMENT, ""))
                    else:
                        parsing_word = True
                        user_args[current_user_args_index] += char
                        parsed_values[parsed_values_index] = (UserInputType.ARGUMENT, user_args[current_user_args_index])
        else:
            if parsing_user_command:
                # Handle case (e.g.,`$ echo' asd'` -> `echo asd: command not found`)
                if parsing_string_literal:
                    if char == "'":
                        parsing_string_literal = False
                        user_command_complete = True
                        parsed_values_index += 1
                        parsed_values.append((UserInputType.COMMAND, ""))
                    else:
                        user_command += char
                        parsed_values[parsed_values_index] = (UserInputType.COMMAND, user_command)
                else:
                    if char == " ":
                        if parsing_word:
                            parsing_word = False
                            parsing_user_command = False
                            user_command_complete = True
                            parsed_values_index += 1
                            parsed_values.append((UserInputType.COMMAND, ""))
                    else:
                        parsing_word = True
                        if char == "'":
                            parsing_string_literal = True
                        else:
                            user_command += char
                            parsed_values[parsed_values_index] = (UserInputType.COMMAND, user_command)
            else:
                # Handle the case where user command is a string literal (enclosed in single quotes)
                if parsing_string_literal:
                    if char == "'":
                        parsing_string_literal = False
                        user_command_complete = True
                        parsed_values_index += 1
                        parsed_values.append((UserInputType.COMMAND, ""))
                    else:
                        user_command += char
                        parsed_values[parsed_values_index] = (UserInputType.COMMAND, user_command)
                else:
                    if char == "'":
                        parsing_string_literal = True
                    else:
                        user_command += char
                        parsed_values[parsed_values_index] = (UserInputType.COMMAND, user_command)
                        parsing_user_command = True
    
    return ParsedUserInput(parsed_values=parsed_values, command=user_command, args=user_args)