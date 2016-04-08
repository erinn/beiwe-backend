from bson import ObjectId

from db.data_access_models import FilesToProcess
from db.study_models import Study
from libs.file_processing_utils import reindex_study
from libs.logging import email_system_administrators

studies = []

if not studies:
    raise Exception("you need to provide some studies")


def do_email( study ):
    email_system_administrators( study.name + " blew up while reindexing",
                                 "Go check on reindex operation.",
                                 source_email="reindexing_error@studies.beiwe.org" )


for study_id in studies:
    if isinstance( study_id, (str, unicode) ):
        study_id = ObjectId( study_id )
    study = Study(study_id)

    print "============================================================="
    print "============================================================="
    print "============================================================="
    print "starting on %s, study id: %s\n" % (study.name, str(study_id))
    print "============================================================="
    print "============================================================="
    print "============================================================="

    if FilesToProcess.count() != 0:
        do_email(study)
        print "stopped on " + str( study_id )
        break

    study_id = ObjectId( study_id )

    try:
        reindex_study(study)
    except Exception as e:
        do_email( study )
        print "stopped on " + str( study_id )
        raise
