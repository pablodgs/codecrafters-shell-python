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
    raw_args: str

def process_user_input(raw_user_input: str) -> ParsedUserInput:
    
    user_input = raw_user_input.strip()
    
    parsing_user_command = False
    user_command_complete = False
    parsing_string_literal = False
    parsing_word = True
    first_space_encountered = False
    
    parsed_values: list[tuple[UserInputType, str]] = [(UserInputType.COMMAND, "")]
    parsed_values_index = 0
    
    user_command: str = ""
    
    raw_args: str = ""
    user_args: list[str] = [""]
    current_user_args_index = 0
    
    user_literal_strings: list[str] = [""]
    current_user_literal_strings_index = 0
    
    last_character_was_quote = False

    for char in user_input:
        if user_command_complete:
            if parsing_string_literal:
                first_space_encountered = False
                if char == "'":
                    parsing_string_literal = False
                    if not last_character_was_quote:
                        current_user_literal_strings_index += 1
                        user_literal_strings.append("")
                        parsed_values_index += 1
                        parsed_values.append((UserInputType.STRING_LITERAL, ""))
                    last_character_was_quote = True
                else:
                    last_character_was_quote = False
                    user_literal_strings[current_user_literal_strings_index] += char
                    raw_args += char
                    parsed_values[parsed_values_index] = (UserInputType.STRING_LITERAL, user_literal_strings[current_user_literal_strings_index])
            else:
                if char == "'":
                    parsing_string_literal = True
                    last_character_was_quote = True
                    first_space_encountered = False
                else:
                    if char == " ":
                        if parsing_word:
                            parsing_word = False
                            current_user_args_index += 1
                            user_args.append("")
                            parsed_values_index += 1
                            parsed_values.append((UserInputType.ARGUMENT, ""))
                        else:
                            if not first_space_encountered:
                                first_space_encountered = True
                                raw_args += char
                    else:
                        first_space_encountered = False
                        parsing_word = True
                        user_args[current_user_args_index] += char
                        raw_args += char
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
        if parsed_values[-1][1] == "":
            parsed_values.pop()
            parsed_values_index -= 1
    return ParsedUserInput(parsed_values=parsed_values, command=user_command, args=user_args, raw_args=raw_args)