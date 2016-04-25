# Open Science Framework extension

This extension connects OpenSesame to the [Open Science Framework](https://osf.io) (OSF), which is a web platform for sharing, connecting, and streamlining scientific workflows. To use it, you will have to [sign up for an account](https://osf.io/login/?sign_up=True) on the OSF website. You can then login to your OSF account from within OpenSesame.

Using this extension, you can link an experiment on your computer to a location in one of your repositories on the OSF. Every time you save your experiment, it will (with your permission) then also be uploaded to this corresponding location. Likewise, you can choose a folder on the OSF to automatically upload data files to after an experiment has finished. You can furthermore directly open experiments that are stored on the OSF from within OpenSesame. When doing so, these experiments will automatically be linked to their corresponding OSF locations, if they weren't already. Beside these features, the extension also offers the possibility to directly interact with your OSF repositories to create or delete folders, and upload, download or delete files.

The OSF website also offers possibilities to connect your projects to other cloud services, among which Dropbox, Google Drive and Github. If you connect your OSF project to one of these services, you can also access them from this extension and interact with them as if they are standard OSF repositories. Pretty sweet, don't you think?

##Logging in to the OSF

To log into the OSF, click on the log in button in OpenSesame's item bar. You need to already have created an account on <https://osf.io> as you cannot do so from OpenSesame. Once logged in, you can open the OSF Explorer, by clicking on your name where the login button used to be and then select *Show explorer*. You will then see a listing of all your projects and repositories/cloud services that you have linked to them.

##Linking an experiment

To link an experiment, you first need to make sure you have already saved this experiment somewhere on your computer. Open up the OSF explorer and select a folder or repository where you would like your experiment to be stored on the OSF. You can either right-click on the folder and select *Sync experiment to this folder* or click *Link experiment* in the button bar at the bottom while the desired folder is selected. 

If succesful, the experiment will be uploaded to the chosen location (you will be prompted with a choice what to do if it already exists) and the OSF node to which the experiment is linked will be shown at the top of the explorer. You can unlink the experiment by clicking the unlink button. You can also choose to automatically upload the experiment on save by checking *Always upload experiment on save*. By doing so, you will no longer be prompted each time for permission to upload the experiment.

When you open an experiment on your computer that is linked to the OSF, OpenSesame will check if the version on your computer and the version on the OSF are the same. If it finds them to be different, you are presented with a dialog offering a choice on how to proceed. You can either keep using the version stored on your computer, or you can continue using the version stored on the OSF. This version will then be downloaded and overwrites the experiment on your computer. However, before it does so you will be asked if you'd like to backup your local file withe a different filename.

##Linking a folder to upload data files to

To link a folder to upload data files to, your experiment needs to be already saved somewhere on your computer. Open up the OSF explorer, right-click on the folder you want to link and select *Sync data to this folder*, or select the folder and click *Link data* in the button bar at the bottom.

If succesful, the OSF node representing the linked folder on the OSF will be shown at the top of the explorer. You can unlink the data folder by clicking the unlink button next to it. You can also choose to automatically upload the data  *Always upload collected data*. By doing so, you will no longer be prompted each time for permission to upload data.

##Opening an experiment stored on the OSF

To open an experiment that is stored on the OSF, find the experiment in the OSF Explorer, right-click on it and select *Open experiment*. Alternatively you can select the experiment and click *Open* in the button bar at the bottom.
Only experiments with the newer .osexp extension (from OpenSesame 3 on) can be directly opened from the OSF.


