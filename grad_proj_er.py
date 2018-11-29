from sqlalchemy import Column, Integer, ForeignKey, UnicodeText, Text, Boolean, DateTime, Unicode, String, Table
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import sys

'''
I stole this template from:
Example of NewsMeme (open source forum like hacker news or Reddit).
# Adapted from https://bitbucket.org/danjac/newsmeme (newsmeme / newsmeme / models)
But, to get the 'lc' and 'rc' attributes of ForeignKey to work, you have to patch eralchemy and sqlalchemy
I suggest doing all this in a virtual environment, that'll make this a lot easier:
https://docs.python.org/3/library/venv.html
This next stuff is links to the repos and the patches you need
https://github.com/zzzeek/sqlalchemy.git
diff --git a/lib/sqlalchemy/sql/schema.py b/lib/sqlalchemy/sql/schema.py
index 67d258b..00f2a4d 100644
--- a/lib/sqlalchemy/sql/schema.py
+++ b/lib/sqlalchemy/sql/schema.py
@@ -1548,7 +1548,7 @@ class ForeignKey(DialectKWArgs, SchemaItem):
		 def __init__(self, column, _constraint=None, use_alter=False, name=None,
									onupdate=None, ondelete=None, deferrable=None,
									initially=None, link_to_name=False, match=None,
-								 info=None,
+								 info=None, lc='*', rc='*', label=None,
									**dialect_kw):
				 Construct a column-level FOREIGN KEY.
@@ -1656,6 +1656,9 @@ class ForeignKey(DialectKWArgs, SchemaItem):
				 self.deferrable = deferrable
				 self.initially = initially
				 self.link_to_name = link_to_name
+				self.rc=rc
+				self.lc=lc
+				self.label=label
				 self.match = match
				 if info:
						 self.info = info


And here's the eralchemy stuff:
https://github.com/Alexis-benoist/eralchemy.git
diff --git a/eralchemy/models.py b/eralchemy/models.py
index 30221cc..e279e13 100644
--- a/eralchemy/models.py
+++ b/eralchemy/models.py
@@ -94,19 +94,21 @@ class Relation(Drawable):
						 left_cardinality=match.group('left_cardinality'),
				 )

-		def __init__(self, right_col, left_col, right_cardinality=None, left_cardinality=None):
+		def __init__(self, right_col, left_col, right_cardinality=None, left_cardinality=None, label=""):
				 if right_cardinality not in self.cardinalities.keys() \
								 or left_cardinality not in self.cardinalities.keys():
						 raise ValueError('Cardinality should be in {}"'.format(self.cardinalities.keys()))
				 self.right_col = right_col
				 self.left_col = left_col
+				self.label = label
				 self.right_cardinality = right_cardinality
				 self.left_cardinality = left_cardinality

		 def to_markdown(self):
-				return "{} {}--{} {}".format(
+				return "{} {}--{}--{} {}".format(
						 self.left_col,
						 self.left_cardinality,
+						self.label,
						 self.right_cardinality,
						 self.right_col,
				 )
@@ -126,7 +128,10 @@ class Relation(Drawable):
				 if self.right_cardinality != '':
						 cards.append('head' +
													self.graphviz_cardinalities(self.right_cardinality))
-				return '"{}" -- "{}" [{}];'.format(self.left_col, self.right_col, ','.join(cards))
+				if self.label==None:
+					return '"{}" -- "{}" [{}];'.format(self.left_col, self.right_col, ','.join(cards))
+				else:
+					return '"{}" -- "{}" [{}];'.format(self.left_col, self.right_col, ','.join(cards)+",label=\""+self.label+"\"")

		 def __eq__(self, other):
				 if Drawable.__eq__(self, other):
diff --git a/eralchemy/sqla.py b/eralchemy/sqla.py
index 137c1ad..7a7a0c7 100644
--- a/eralchemy/sqla.py
+++ b/eralchemy/sqla.py
@@ -16,8 +16,9 @@ def relation_to_intermediary(fk):
		 return Relation(
				 right_col=format_name(fk.parent.table.fullname),
				 left_col=format_name(fk._column_tokens[1]),
-				right_cardinality='?',
-				left_cardinality='*',
+				label=fk.label,
+				right_cardinality=fk.rc,#'?',
+				left_cardinality=fk.lc#'*',
		 )

If you don't want to patch this stuff (I don't blame you) just remove all the 'lc' 'rc' variables here
Oh, also 'label' parts of ForeignKey
Don't forget to hide crypto repos you don't want!:
	update "gitsec.CryptoProvidingRepo" set hide_from_ui=1 where repo_name='nss-dev/nss';
'''
Base = declarative_base()
fake_schema=None
latex=False
er=False
schema=False
if len(sys.argv)==2:
	if sys.argv[1]=='schema':
		fake_schema="gitsec."
		schema=True
	if sys.argv[1]=='er':
		fake_schema=""
		er=True
	if sys.argv[1]=='latex_schema':
		fake_schema="gitsec."
		latex=True
	
if fake_schema==None:
	print("Specify whether you want the schema or er diagram")
	print(""+sys.argv[0]+" schema")
	print(""+sys.argv[0]+" er")
	sys.exit(1)

class Organization(Base):
		__tablename__ = fake_schema+"Organization"
		name = Column(String(200), primary_key=True)
		created_at = Column(Integer)
		company = Column(String(200))

class User(Base):
		__tablename__ = fake_schema+"User"
		name = Column(String(200), primary_key=True)
		joined_at = Column(Integer)
		num_repos = Column(Integer)
		followers = Column(Integer)
		following = Column(Integer)

class Topic(Base):
		__tablename__ = fake_schema+"Topic"
		topic_name = Column(String(200), primary_key=True)
		is_security_related = Column(Integer)

class RelatedToTopic(Base):
		__tablename__ = fake_schema+"RelatedToTopic"
		topic_name = Column(String(200), ForeignKey(fake_schema+"Topic.topic_name", lc='1', rc='*'), primary_key=True)
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='*'), primary_key=True)

class CryptoFunction(Base):
		__tablename__ = fake_schema+"CryptoFunction"
		function_name = Column(String(200), primary_key=True)

class UsageIndicator(Base):
		__tablename__ = fake_schema+"UsageIndicator"
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='*'), primary_key=True)
		keyword = Column(String(200), primary_key=True)

class ProvidesFunction(Base):
		__tablename__ = fake_schema+"ProvidesFunction"
		function_name = Column(String(200), ForeignKey(fake_schema+"CryptoFunction.function_name", lc='1', rc='*'), primary_key=True)
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='*'), primary_key=True)

class Language(Base):
		__tablename__ = fake_schema+"Language"
		language_name = Column(String(200), primary_key=True)

class UsesLanguage(Base):
		__tablename__ = fake_schema+"UsesLanguage"
		language_name = Column(String(200), ForeignKey(fake_schema+"Language.language_name", lc='1', rc='*'), primary_key=True)
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='*'), primary_key=True)
		instances = Column(Integer)

class ContributedTo(Base):
		__tablename__ = fake_schema+"ContributedTo"
		user_name = Column(String(200), ForeignKey(fake_schema+"User.name", lc='1', rc='*'), primary_key=True)
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='*'), primary_key=True)

class Repo(Base):
		__tablename__ = fake_schema+"Repo"
		full_name = Column(String(200), primary_key=True)
		owner = Column(String(200), ForeignKey(fake_schema+"User.name", lc='1', rc='*'))
		forks = Column(Integer)
		forked_from = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='*', label="forked_from"))
		bugs = Column(Integer)
		stars = Column(Integer)
		created_at = Column(Integer)
		subscribers = Column(Integer)
		pulls = Column(Integer)
		organization_name = Column(String(200), ForeignKey(fake_schema+"Organization.name", lc='1', rc='*'))

class CryptoProvidingRepo(Base):
		__tablename__ = fake_schema+"CryptoProvidingRepo"
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='1', label="isa"), primary_key=True)
		license = Column(String(200))

class CryptoUsingLibrary(Base):
		__tablename__ = fake_schema+"CryptoUsingRepo"
		repo_name = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='1', rc='1', label="isa"), primary_key=True)
		type = Column(Integer, nullable=False)

class UsesCryptoLibrary(Base):
		__tablename__ = fake_schema+"UsesCryptoLibrary"
		library = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='*', rc='1'), primary_key=True)
		crypto_library = Column(String(200), ForeignKey(fake_schema+"Repo.full_name", lc='*', rc='1'), primary_key=True)
		num_indicators = Column(Integer, nullable=False)

if __name__ == '__main__':
		from eralchemy import render_er

		if er:
			print("Rendering to ./scott_griffy_grad_proj_er_sub2.pdf")
			render_er(Base, 'scott_griffy_grad_proj_er_sub2.pdf')
		if latex:
			print("\\begin{lstlisting}")
		if latex or schema:
			print(str(CreateTable(CryptoUsingLibrary.__table__))+";")
			print(str(CreateTable(CryptoProvidingRepo.__table__))+";")
			print(str(CreateTable(Repo.__table__))+";")
			print(str(CreateTable(ContributedTo.__table__))+";")
			print(str(CreateTable(UsesLanguage.__table__))+";")
			print(str(CreateTable(ProvidesFunction.__table__))+";")
			print(str(CreateTable(Language.__table__))+";")
			print(str(CreateTable(CryptoFunction.__table__))+";")
			print(str(CreateTable(RelatedToTopic.__table__))+";")
			print(str(CreateTable(Topic.__table__))+";")
			print(str(CreateTable(User.__table__))+";")
			print(str(CreateTable(Organization.__table__))+";")
			print(str(CreateTable(UsageIndicator.__table__))+";")
			print(str(CreateTable(UsesCryptoLibrary.__table__))+";")
			print(str("insert into \""+fake_schema+"Organization\" (name) values ('no_organization');"))
		if latex:
			print("\\end{lstlisting}")
