# Python Reccommender code for use on Azure ml studio
class Recc:

    def __init__(self,DataFrame1):
        # reading in new user data. Use try catch

        self.stud_scores = DataFrame1.iloc[0,:]
        self.stud_subjects = DataFrame1.iloc[1,:]

    # Function to check if correlating users/Courses exist
    @staticmethod
    def check_sub(old_data, stud_subjects):
        corr_users = []
        stud_sub = stud_subjects[:,:]

        for index, row in old_data.iterrows():
            if len(set(row).intersection(stud_sub)) >= 2:
                corr_users.append(index)
        return corr_users

    def user_user(self, users_features, users_scores, users_rating, corr_users, stud_scores):

        import pandas as pd
        import numpy as np

        self.users_features = users_features
        self.users_rating = users_rating
        self.users_scores = users_scores


        # Making a 5 point normalized series out of user data 
        stud_scores_series = pd.Series(
            stud_scores,
            index=["best subject1", "best subject2", "best subject3"],
            name="User")
        stud_scores_series = (pd.to_numeric(stud_scores_series) / 100) * 5

        # Calculating the correlation between old user scores and new user scores in order to
        # Get users with high correlation  
        user_corrcoeff = {}
        old_users = ((self.users_scores.loc[corr_users, :]) / 100) * 5
        #print('Old users are %s' % old_users)
        #print("Student score series is %s" %stud_scores_series)

        for index, row in old_users.iterrows():
            user_corrcoeff[index] = stud_scores_series.corr(row)
        #print(user_corrcoeff)

        # Sorting dictionary to get index of top 3 users with highest correlation
        top_corr_users = []
        #print('Sort by items:')
        for key, value in sorted(user_corrcoeff.items(), key=lambda item: (item[1], item[0]), reverse=True)[0:3]:
            #print("{}: {}".format(key, value))
            top_corr_users.append(key)

        #print("Top correlating users are %s" % top_corr_users)

        # Now, to actually give recommendation From
        # the most highly rated courses of the users with the highest correlation 
        # First, locate user data in the course ratings dataframe. 
        # then sort according to ratings to get the courses with the highest ratings 
        # finally, return the top 5 courses with highest ratings
        top = self.users_rating.loc[top_corr_users, :].sort_values(
            'ratings', ascending=False, inplace=False).head(5)
        #print(top)

        recommendation = top[:]["CourseName"].values
        #print(recommendation)

        return recommendation

    def user_item(self,course_sub, stud_scores, stud_subjects):

        #self.course_features = course_features
        import pandas as pd
        import numpy as np
        self.course_sub = course_sub
        self.stud_subjects=stud_subjects.tolist()
        self.stud_scores=stud_scores.tolist()

        # Making a 5 point normalized series out of user data and 
        # appending to courses dataframe for shape normalization
        # Then deleting from the courses df 

        stud_scores_ser = pd.Series(
            self.stud_scores, index=self.stud_subjects,
            dtype=np.float64, name="User")
        stud_scores_norm = (pd.to_numeric(stud_scores_ser) / 100) * 5
        #print("Stud scores normalized is %s" % stud_scores_norm)
        self.course_sub = self.course_sub.append(
            stud_scores_norm, ignore_index=False) # , sort=False)
        self.course_sub.fillna(0, axis=0, inplace=True)
        stud_series = self.course_sub.loc["User"][:]
        self.course_sub.drop(self.course_sub.index[-1], inplace=True)
        

        # Calculating the correlation between all courses and user data in order to
        # Get courses with high correlation

        #corr_courses = self.check_sub(course_features, stud_subjects)
        # print ("Correlating courses are %s" %corr_courses)
        course_corrcoeff = {}
        #alike_courses = self.course_sub.loc[corr_courses, :]
        # print ("Dataframe of Correlating courses are %s" %alike_courses)

        for index, row in self.course_sub.iterrows():
            course_corrcoeff[index] = stud_series.corr(row)
        #print("Course corr coeff is %s" % course_corrcoeff)

        #top_corr_courses=pd.Series(course_corrcoeff).sort_values(ascending=False).iloc[:5].index
        top_corr_courses=pd.Series(course_corrcoeff).sort_values(ascending=False).iloc[:5].index.tolist()
        #top_corr_courses=pd.Series(course_corrcoeff).sort_values(ascending=False).index.tolist()
        #top_corr_courses=top_corr_courses.to_frame(name="result")
        result=pd.DataFrame(top_corr_courses, columns=["recommendation"])

        return result


def mymain(DataFrame1, DataFrame2):
    # Main fucntion to implement in Azure ml studio 

    # Importing libraries
    import pandas as pd
    import numpy as np
    import pyodbc


    #stud_scores=[89, 67, 52, 45]
    #stud_subjects=[89, "Mathematics", "Chemistry", "Agricultural Science"]

    stud_scores= DataFrame1.iloc[0,:3]
    stud_subjects = DataFrame1.iloc[0,3:]

    users = False
    try:
        # creating database object and cursor
        server = 'tcp:wb-learningdb.database.windows.net'
        database= 'WB-LearningDB'
        username='wbuser'
        password='wbsidmach@123'
        driver= '{ODBC Driver 17 for SQL Server}'
        cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = cnxn.cursor()
        # reading in data from db  
        users_features=pd.read_sql_query("SELECT * FROM student_subjectname",cnxn, index_col="user ID")
        users_scores=pd.read_sql_query("SELECT * FROM student_subjectscore",cnxn, index_col="user ID")
        users_rating=pd.read_sql_query("SELECT * FROM student_courserating",cnxn, index_col="user ID")
        
        cnxn.close()
        corr_users = Recc.check_sub(users_features, stud_subjects)
        if len(corr_users) < 10: 
            raise Exception("")
        users = True
    except Exception as ex:
        try:
            #course_sub = pd.read_csv("course_subject_matrix.csv")
            #course_features = pd.read_excel("subject_courses.xlsx")
            course_sub = DataFrame2.iloc[:,:]
            # Setting "CourseName" as index and making a series out of user data
            #course_features.set_index("CourseName", inplace=True)
            course_sub.set_index("CourseName", inplace=True)

        except Exception as rec:
            print(rec)
            raise Exception("An error occurred, please try again later")

    # Instantiate an object of the class
    recc_obj = Recc(DataFrame1)

    if users:
        #print("Correlating users are %s" % corr_users)
        rec = recc_obj.user_user(users_features, users_scores, users_rating, corr_users, stud_scores)
    else:
        rec = recc_obj.user_item(course_sub)

    print(rec)
    return rec
