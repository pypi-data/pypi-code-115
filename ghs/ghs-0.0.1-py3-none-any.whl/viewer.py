import colorama
from termcolor import cprint

colorama.init()


def print_top_contribution(final_data):
  text = f"\nYour Top Contributions:\n"
  print(text)
  output_text = text
  count = 0
  for i in final_data.keys():
    count += 1
    if count > 3:
      break
    repo_name = i
    repo_owner = final_data[i]['repo_owner']
    total_commits = final_data[i]['total_commits']
    contributors_count = final_data[i]['contributors_count']
    individual_commit_countribution = final_data[i]['individual_commit_contribution']
    languages = final_data[i]['languages']
    is_private = final_data[i]['is_private']
    stargazer_count = final_data[i]['stargazer_count']
    fork_count = final_data[i]['fork_count']

    text = f"{count}.) "
    print(text, end="")
    output_text += text

    if is_private:
      text = f"private repo belonging to {repo_owner}\n"
      cprint(text, 'green', end="")
      output_text += text
    else:
      text = f"{repo_owner}/{repo_name}\n"
      cprint(text, 'green', end="")
      output_text += text

    if total_commits is not None:
      text = f"\t * This repository has a total of {total_commits} commits{f' and {contributors_count} contributors' if contributors_count is not None else ''}.\n"
      print(text, end="")
      output_text += text
    if stargazer_count > 0:
      text = f"\t * It has {stargazer_count} stars{f' and {fork_count} forks' if fork_count > 0 else ''}.\n"
      print(text, end="")
      output_text += text

    text = f"\t * During this period you made {individual_commit_countribution} commits to this repo.\n\t * Top languages of the repo {languages}.\n"
    print(text, end="")
    output_text += text

  return output_text
