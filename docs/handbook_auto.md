(auto_run)=
# Running the automatic workflow

This workflow is not advised for users that are starting to learn how to process multiparametric MRI data. We recommend to learn how to use the interactive workflow first to fammiliarize with Resomapper and the whole pipeline.

This automatic workflow will run the same steps as the interactive workflow, but specifying first the options you want to use. You will have to prepare a JSON file specifying for each modality what kind of preprocessing you need. You can create a template of this JSON and modify it by running the command:

```
resomapper_tools
```

And selecting the first option.

Once you have your data and options JSON prepared, with this command, you will be able to launch the batch processing. You can redirect the standard exit of the terminal to a log file, if you want.

```
resomapper_auto -d [working_directory_path] -j [options_json_path]
```